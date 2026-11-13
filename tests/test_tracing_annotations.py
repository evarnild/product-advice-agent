"""§10: `LangfuseAnnotations` against a faked SDK `.api` object (B6, B7, B9, B10, B13, AC5-AC7)."""

import json
from datetime import UTC, datetime, timedelta

import pytest

from advisor import tracing
from advisor.evals.annotate import AnnotationError, RunTrace, Score
from advisor.tracing import LangfuseAnnotations, make_annotations
from tests.fake_langfuse_api import (
    T0,
    FakeApi,
    config,
    item,
    obs,
    queue,
    score,
)

TAGS = ["eval", "run:S1", "case:a"]


def annotations(api, secrets=()):
    return LangfuseAnnotations(api, secrets=secrets)


# --- B6 score config ------------------------------------------------------


def test_a_missing_config_is_created_as_boolean_pass_with_a_description():
    api = FakeApi(configs=[[config("c1", "other")]])
    assert annotations(api).ensure_score_config() == "cfg-new"
    (kwargs,) = api.called("score_configs.create")
    assert kwargs == {
        "name": "pass",
        "data_type": "BOOLEAN",
        "description": "pass/fail label; the critique goes in the comment",
    }


def test_the_boolean_pass_config_is_reused_not_a_numeric_one_listed_first():
    api = FakeApi(
        configs=[
            [config("n1", "pass", "NUMERIC")],
            [config("x", "other"), config("b1", "pass"), config("b2", "pass")],
        ]
    )
    assert annotations(api).ensure_score_config() == "b1"
    assert api.called("score_configs.create") == []
    assert [kw["page"] for kw in api.called("score_configs.get")] == [1, 2]
    assert all(kw["limit"] == 100 for kw in api.called("score_configs.get"))


def test_a_pass_config_of_another_type_only_is_a_conflict_naming_the_type():
    api = FakeApi(configs=[[config("n1", "pass", "NUMERIC")]])
    with pytest.raises(AnnotationError) as caught:
        annotations(api).ensure_score_config()
    assert caught.value.step == "config"
    assert "NUMERIC" in caught.value.message and "pass" in caught.value.message
    assert api.called("score_configs.create") == []


# --- B7 queue -------------------------------------------------------------


def test_a_missing_queue_is_created_with_the_config_id():
    api = FakeApi(queues=[[queue("q0", "other", ["cfg"])]])
    assert annotations(api).ensure_queue("advisor-eval S1", "cfg") == "q-new"
    (kwargs,) = api.called("annotation_queues.create_queue")
    assert kwargs["name"] == "advisor-eval S1"
    assert kwargs["score_config_ids"] == ["cfg"]
    assert isinstance(kwargs["description"], str) and kwargs["description"]


def test_an_existing_queue_is_found_by_name_on_a_later_page_and_reused():
    api = FakeApi(
        queues=[[queue("q0", "other", ["cfg"])], [queue("q1", "advisor-eval S1", ["x", "cfg"])]]
    )
    assert annotations(api).ensure_queue("advisor-eval S1", "cfg") == "q1"
    assert api.called("annotation_queues.create_queue") == []


def test_an_existing_queue_without_the_pass_config_is_a_conflict():
    api = FakeApi(queues=[[queue("q1", "advisor-eval S1", ["other-config"])]])
    with pytest.raises(AnnotationError) as caught:
        annotations(api).ensure_queue("advisor-eval S1", "cfg")
    assert caught.value.step == "queue"
    assert "advisor-eval S1" in caught.value.message
    assert api.called("annotation_queues.create_queue") == []


def test_find_queue_returns_the_id_or_none_and_never_creates():
    api = FakeApi(queues=[[queue("q1", "mine")]])
    assert annotations(api).find_queue("mine") == "q1"
    assert annotations(api).find_queue("absent") is None
    assert api.called("annotation_queues.create_queue") == []


# --- B9 run traces --------------------------------------------------------


def test_run_traces_filters_on_tags_root_and_follows_the_cursor():
    api = FakeApi(
        observations=[
            [obs("t1", TAGS, T0)],
            [obs("t2", ["eval", "run:S1", "case:b"], T0 + timedelta(minutes=1))],
        ]
    )
    traces = annotations(api).run_traces("S1")
    assert traces == [
        RunTrace("t1", tuple(TAGS), T0),
        RunTrace("t2", ("eval", "run:S1", "case:b"), T0 + timedelta(minutes=1)),
    ]
    first, second = api.called("observations.get_many")
    assert json.loads(first["filter"]) == [
        {
            "type": "arrayOptions",
            "column": "traceTags",
            "operator": "all of",
            "value": ["eval", "run:S1"],
        },
        {"type": "boolean", "column": "isRootObservation", "operator": "=", "value": True},
    ]
    assert first["fields"] == "core,basic,trace_context"
    assert first["limit"] == 1000
    assert "cursor" not in first or first["cursor"] is None
    assert second["cursor"] == "c1"
    assert second["filter"] == first["filter"]


def test_a_naive_start_time_is_read_as_utc():
    naive = datetime(2026, 11, 12, 10, 0, 0)
    api = FakeApi(observations=[[obs("t1", TAGS, naive)]])
    (trace,) = annotations(api).run_traces("S1")
    assert trace.start_time == datetime(2026, 11, 12, 10, 0, 0, tzinfo=UTC)


def test_an_observation_without_tags_has_empty_tags():
    api = FakeApi(observations=[[obs("t1", [])]])
    (trace,) = annotations(api).run_traces("S1")
    assert trace.tags == ()


# --- B10 items ------------------------------------------------------------


def test_queued_trace_ids_are_the_trace_items_across_pages():
    api = FakeApi(items=[[item("t1"), item("o1", "OBSERVATION")], [item("t2")]])
    assert annotations(api).queued_trace_ids("q1") == {"t1", "t2"}
    calls = api.called("annotation_queues.list_queue_items")
    assert [kw["page"] for kw in calls] == [1, 2]
    assert all(kw["queue_id"] == "q1" and kw["limit"] == 100 for kw in calls)


def test_add_trace_creates_one_trace_item():
    api = FakeApi()
    annotations(api).add_trace("q1", "t9")
    (kwargs,) = api.called("annotation_queues.create_queue_item")
    assert kwargs == {"queue_id": "q1", "object_id": "t9", "object_type": "TRACE"}


# --- B13 scores -----------------------------------------------------------


def test_annotation_scores_ask_for_the_queue_and_follow_the_cursor():
    later = T0 + timedelta(minutes=3)
    api = FakeApi(
        scores=[
            [score("t1", True, None, T0)],
            [score("t2", False, "wrong price", later)],
        ]
    )
    scores = annotations(api).annotation_scores("q1")
    assert scores == [Score("t1", True, "", T0), Score("t2", False, "wrong price", later)]
    first, second = api.called("scores.get_many")
    assert first["source"] == "ANNOTATION"
    assert first["queue_id"] == "q1"
    assert first["name"] == "pass"
    assert first["fields"] == "details,subject"
    assert first["limit"] == 100
    assert second["cursor"] == "c1"
    assert {k: v for k, v in second.items() if k != "cursor"} == {
        k: v for k, v in first.items() if k != "cursor"
    }


def test_scores_that_are_not_a_boolean_on_a_trace_are_skipped():
    api = FakeApi(
        scores=[
            [
                score("t1", True),
                score("t2", 1.0, data_type="NUMERIC"),
                score("o1", True, kind="observation"),
                score("t3", "yes", data_type="TEXT"),
            ]
        ]
    )
    assert [s.trace_id for s in annotations(api).annotation_scores("q1")] == ["t1"]


# --- errors ---------------------------------------------------------------


@pytest.mark.parametrize(
    ("method", "step", "call"),
    [
        ("score_configs.get", "config", lambda a: a.ensure_score_config()),
        ("annotation_queues.list_queues", "queue", lambda a: a.ensure_queue("n", "c")),
        ("annotation_queues.list_queues", "queue", lambda a: a.find_queue("n")),
        ("observations.get_many", "traces", lambda a: a.run_traces("S1")),
        ("annotation_queues.list_queue_items", "items", lambda a: a.queued_trace_ids("q")),
        ("annotation_queues.create_queue_item", "add", lambda a: a.add_trace("q", "t")),
        ("scores.get_many", "scores", lambda a: a.annotation_scores("q")),
    ],
)
def test_an_sdk_error_becomes_an_annotation_error_with_type_and_message(method, step, call):
    api = FakeApi(configs=[[]], queues=[[]], items=[[]], observations=[[]], scores=[[]])
    api.error_on[method] = ConnectionError("down")
    with pytest.raises(AnnotationError) as caught:
        call(annotations(api))
    assert caught.value.step == step
    assert caught.value.message == "ConnectionError: down"
    assert str(caught.value) == f"Langfuse {step} failed: ConnectionError: down"


def test_a_secret_in_an_sdk_error_is_redacted():
    api = FakeApi(scores=[[]])
    api.error_on["scores.get_many"] = RuntimeError("401 for sk-lf-secret via pk-lf-public")
    with pytest.raises(AnnotationError) as caught:
        annotations(api, secrets=("sk-lf-secret", "pk-lf-public")).annotation_scores("q")
    assert "sk-lf-secret" not in str(caught.value) and "pk-lf-public" not in str(caught.value)
    assert "401" in str(caught.value)


# --- make_annotations -----------------------------------------------------

ENV = {
    "LANGFUSE_PUBLIC_KEY": "pk-test",
    "LANGFUSE_SECRET_KEY": "sk-test",
    "LANGFUSE_HOST": "http://langfuse.test:3000",
}


@pytest.mark.parametrize("missing", list(ENV))
def test_make_annotations_refuses_when_a_variable_is_missing(monkeypatch, missing):
    built = []
    monkeypatch.setattr(tracing, "Langfuse", lambda **kw: built.append(kw))
    env = {k: v for k, v in ENV.items() if k != missing}
    with pytest.raises(AnnotationError) as caught:
        make_annotations(env)
    assert missing in caught.value.message
    assert built == []


def test_make_annotations_builds_one_client_with_the_values_and_uses_its_api(monkeypatch):
    api = FakeApi(configs=[[config("b1", "pass")]])
    built = []

    class Client:
        def __init__(self, **kw):
            built.append(kw)
            self.api = api

    monkeypatch.setattr(tracing, "Langfuse", Client)
    assert make_annotations(ENV).ensure_score_config() == "b1"
    assert built == [
        {
            "public_key": "pk-test",
            "secret_key": "sk-test",
            "host": "http://langfuse.test:3000",
        }
    ]


def test_a_client_that_cannot_be_built_is_a_config_error_without_the_key(monkeypatch):
    def boom(**kw):
        raise ValueError(f"bad key {kw['secret_key']}")

    monkeypatch.setattr(tracing, "Langfuse", boom)
    with pytest.raises(AnnotationError) as caught:
        make_annotations(ENV)
    assert caught.value.step == "config"
    assert "sk-test" not in str(caught.value) and "ValueError" in str(caught.value)

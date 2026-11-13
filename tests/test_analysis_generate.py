import json

import pytest

from advisor.catalogue import load_catalogue
from advisor.evals.cases import parse_cases
from advisor.evals.generate import (
    build_prompt,
    case_lines,
    dumps_cases,
    generate,
    summary,
)
from advisor.evals.modeljson import extract_json
from advisor.models.base import ModelError, ModelNotAvailableError, ModelTurn, ModelUnreachableError
from advisor.models.fake import ScriptedModelClient

CAT = load_catalogue()
STUDENT = "a student on a tight budget"
GIFT = "someone buying a gift"

HP = ("headphones", "exact-match", STUDENT)
LOW = ("laptop", "budget-too-low", GIFT)
OFF = ("off-topic", "off-topic", GIFT)
OOS = ("headphones", "out-of-stock", STUDENT)


def reply(*items, prefix="", suffix=""):
    return ModelTurn(text=prefix + json.dumps(list(items)) + suffix)


def q(question, **probe):
    return {"question": question, "probe": probe}


GOOD_HP = reply(
    q("Any headphones for 59 euros or less?", category="headphones", max_price=59),
    q("Cheap headphones under sixty?", category="headphones", max_price=59),
)


def test_the_prompt_gives_the_cell_the_categories_with_prices_and_the_out_of_stock_products():
    prompt = build_prompt(("laptop", "out-of-stock", GIFT), CAT)
    assert "laptop" in prompt and "out-of-stock" in prompt and GIFT in prompt
    assert "- headphones: 6 products, 59.0 to 249.0" in prompt
    for pid in ("P-004", "P-010", "P-017", "P-024", "P-032"):
        assert f"- {pid}, " in prompt
    assert "Sonavo Quiet Pro" in prompt
    assert "[[" not in prompt
    assert "never write the" in prompt  # questions only, no answers


def test_one_model_call_per_cell_with_no_tools_and_the_cell_in_the_prompt():
    client = ScriptedModelClient([GOOD_HP, reply()])
    generate([HP, OFF], client, CAT)
    assert len(client.requests) == 2
    first = client.requests[0]
    assert first.tools == ()
    assert "exact-match" in first.messages[0].text
    assert "off-topic" in client.requests[1].messages[0].text


def test_a_valid_candidate_is_kept_and_an_invalid_one_dropped_with_its_reason():
    client = ScriptedModelClient(
        [
            reply(
                q("Headphones up to 59?", category="headphones", max_price=59),
                q("Headphones up to 58?", category="headphones", max_price=58),
            )
        ]
    )
    result = generate([HP], client, CAT)
    assert [c.question for c in result.kept] == ["Headphones up to 59?"]
    stats = result.stats["exact-match"]
    assert (stats.asked, stats.kept, stats.dropped) == (2, 1, ["the probe matches no product"])


def test_prose_and_think_blocks_around_the_json_are_tolerated():
    text = "<think>hmm [1] {x}</think>Sure! Here you go:\n```json\n" + GOOD_HP.text + "\n```\nBye"
    result = generate([HP], ScriptedModelClient([ModelTurn(text=text)]), CAT)
    assert len(result.kept) == 2


def test_an_unparsable_answer_is_dropped_and_counted():
    client = ScriptedModelClient([ModelTurn(text="I cannot do that."), GOOD_HP])
    result = generate([HP, HP], client, CAT)
    assert result.stats["exact-match"].dropped == ["unparsable model answer"] * 2
    assert result.stats["exact-match"].kept == 2


def test_a_malformed_candidate_and_a_malformed_probe_are_dropped():
    client = ScriptedModelClient(
        [reply({"probe": {}}, {"question": "x?", "probe": {"category": "toaster"}})]
    )
    result = generate([HP], client, CAT)
    assert result.kept == []
    assert sorted(result.stats["exact-match"].dropped) == ["no probe", "no question text"]


def test_missing_candidates_and_extra_candidates():
    one = reply(q("Headphones up to 59?", category="headphones", max_price=59))
    result = generate([HP], ScriptedModelClient([one]), CAT)
    assert result.stats["exact-match"].dropped == ["missing from the model answer"]
    three = reply(
        *[q(f"Headphones up to 59 v{i}?", category="headphones", max_price=59) for i in range(3)]
    )
    result = generate([HP], ScriptedModelClient([three]), CAT)
    assert len(result.kept) == 2  # two a cell, the third is not considered


def test_a_repeated_question_is_dropped():
    same = reply(
        q("Headphones up to 59?", category="headphones", max_price=59),
        q("headphones UP TO 59?", category="headphones", max_price=59),
    )
    result = generate([HP], ScriptedModelClient([same]), CAT)
    assert len(result.kept) == 1
    assert result.stats["exact-match"].dropped == ["duplicate question"]


def test_off_topic_needs_no_probe_and_out_of_stock_needs_the_product():
    client = ScriptedModelClient(
        [
            reply({"question": "What is the weather?"}, {"question": "Tell me a joke."}),
            reply(
                q("Is the Sonavo Quiet Pro back?", product_id="P-004"),
                q("Is the Auralis Calm 300 out?", product_id="P-001"),
            ),
        ]
    )
    result = generate([OFF, OOS], client, CAT)
    assert result.stats["off-topic"].kept == 2
    assert result.stats["out-of-stock"].kept == 1
    assert "in stock" in result.stats["out-of-stock"].dropped[0]


def test_the_first_unreachable_call_raises_but_a_later_one_is_a_drop():
    with pytest.raises(ModelUnreachableError):
        generate([HP], ScriptedModelClient([ModelUnreachableError("down")]), CAT)
    with pytest.raises(ModelNotAvailableError):
        generate([HP], ScriptedModelClient([ModelNotAvailableError("no model")]), CAT)
    client = ScriptedModelClient([GOOD_HP, ModelUnreachableError("down"), ModelError("boom")])
    result = generate([HP, HP, HP], client, CAT)
    assert result.stats["exact-match"].kept == 2
    assert result.stats["exact-match"].dropped == [
        "model unavailable: ModelUnreachableError",
        "model unavailable: ModelUnreachableError",
        "model error: ModelError",
        "model error: ModelError",
    ]


def kept_for_all_scenarios():
    client = ScriptedModelClient(
        [
            GOOD_HP,
            reply(
                q("A laptop under 10 euros?", category="laptop", max_price=10),
                q("Laptops for 5 euros?", category="laptop", max_price=5),
            ),
            reply({"question": "What is the weather?"}, {"question": "Tell me a joke."}),
            reply(q("Is the Sonavo Quiet Pro back?", product_id="P-004")),
        ]
    )
    return generate([HP, LOW, OFF, OOS], client, CAT)


def test_cases_have_unique_ids_dimensions_and_the_probe_in_the_note():
    lines = case_lines(kept_for_all_scenarios())
    ids = [line["id"] for line in lines]
    assert ids == [
        "gen-exact-match-1",
        "gen-exact-match-2",
        "gen-budget-too-low-1",
        "gen-budget-too-low-2",
        "gen-off-topic-1",
        "gen-off-topic-2",
        "gen-out-of-stock-1",
    ]
    assert lines[0]["dimensions"] == {
        "feature": "headphones",
        "scenario": "exact-match",
        "persona": STUDENT,
    }
    assert lines[0]["note"] == 'probe: {"category": "headphones", "max_price": 59}'
    assert lines[6]["note"] == 'probe: {"product_id": "P-004"}'


def test_only_off_topic_cases_must_decline_and_none_forces_a_product():
    lines = case_lines(kept_for_all_scenarios())
    for line in lines:
        assert line.get("must_decline", False) == (line["dimensions"]["scenario"] == "off-topic")
        assert "expect_ids" not in line and "forbid_ids" not in line


def test_the_output_parses_with_the_case_parser():
    text = dumps_cases(case_lines(kept_for_all_scenarios()))
    cases = parse_cases(text, CAT)
    assert len(cases) == 7
    assert cases[4].must_decline is True
    assert cases[0].dimensions["feature"] == "headphones"


def test_the_summary_has_a_line_per_scenario_with_reasons():
    client = ScriptedModelClient(
        [
            reply(
                q("Up to 59?", category="headphones", max_price=59),
                q("Up to 58?", category="headphones", max_price=58),
            )
        ]
    )
    assert summary(generate([HP], client, CAT)) == [
        "exact-match: asked 2, kept 1, dropped 1 (1 x the probe matches no product)"
    ]
    assert summary(kept_for_all_scenarios())[0] == "budget-too-low: asked 2, kept 2, dropped 0"


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("x [1, 2] y", [1, 2]),
        ('<think>[9]</think>{"a": 1}', {"a": 1}),
        ("prose [broken", None),
        ("nothing", None),
        ('[bad] {"ok": true}', {"ok": True}),
    ],
)
def test_extract_json_takes_the_first_json_value(text, expected):
    assert extract_json(text) == expected

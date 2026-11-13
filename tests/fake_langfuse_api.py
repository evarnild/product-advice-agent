"""A fake of the Langfuse SDK's `.api` object (5.2.0 shapes), shared by the §10 tests.

It records every call as `(method, kwargs)` and has no delete or update
method, so a test fails if the code ever reaches for one. Pages are given as
lists; the fake serves page `n` (1-based) or follows the cursor `"c<n>"`.
"""

from datetime import UTC, datetime
from types import SimpleNamespace as NS

T0 = datetime(2026, 11, 12, 10, 0, 0, tzinfo=UTC)


def config(cid, name, data_type="BOOLEAN"):
    return NS(id=cid, name=name, data_type=data_type)


def queue(qid, name, config_ids=()):
    return NS(id=qid, name=name, score_config_ids=list(config_ids))


def item(object_id, object_type="TRACE"):
    return NS(object_id=object_id, object_type=object_type)


def obs(trace_id, tags, start=T0):
    return NS(trace_id=trace_id, tags=list(tags), start_time=start)


def score(trace_id, value, comment=None, ts=T0, kind="trace", data_type="BOOLEAN"):
    return NS(
        data_type=data_type,
        value=value,
        comment=comment,
        timestamp=ts,
        subject=NS(kind=kind, id=trace_id),
    )


class _Page:
    def __init__(self, calls, method, pages):
        self._calls, self._method, self._pages = calls, method, pages

    def _record(self, kwargs):
        self._calls.append((self._method, kwargs))


class _Paged(_Page):
    """Page-number pagination: `data` and `meta.total_pages`."""

    def __call__(self, **kwargs):
        self._record(kwargs)
        self._maybe_raise()
        n = kwargs.get("page", 1)
        data = self._pages[n - 1] if n <= len(self._pages) else []
        return NS(data=data, meta=NS(page=n, total_pages=len(self._pages)))

    def _maybe_raise(self):
        pass


class _Cursor(_Page):
    """Cursor pagination: `data` and `meta.cursor`."""

    def __call__(self, *args, **kwargs):
        self._record({"args": args, **kwargs} if args else kwargs)
        n = int(kwargs["cursor"][1:]) if kwargs.get("cursor") else 0
        data = self._pages[n] if n < len(self._pages) else []
        more = f"c{n + 1}" if n + 1 < len(self._pages) else None
        return NS(data=data, meta=NS(cursor=more))


class FakeApi:
    def __init__(
        self,
        *,
        configs=(),
        queues=(),
        items=(),
        observations=(),
        scores=(),
        created_config_id="cfg-new",
        created_queue_id="q-new",
    ):
        self.calls = []
        self.error_on = {}  # method name -> exception to raise
        c = self.calls

        def make(cls, method, pages):
            def run(*args, **kwargs):
                if method in self.error_on:
                    c.append((method, kwargs))
                    raise self.error_on[method]
                return cls(c, method, pages)(*args, **kwargs)

            return run

        def create_config(**kwargs):
            c.append(("score_configs.create", kwargs))
            if "score_configs.create" in self.error_on:
                raise self.error_on["score_configs.create"]
            return NS(id=created_config_id)

        def create_queue(**kwargs):
            c.append(("annotation_queues.create_queue", kwargs))
            return NS(id=created_queue_id)

        def create_item(queue_id, **kwargs):
            c.append(("annotation_queues.create_queue_item", {"queue_id": queue_id, **kwargs}))
            if "annotation_queues.create_queue_item" in self.error_on:
                raise self.error_on["annotation_queues.create_queue_item"]
            return NS(id="item")

        self.score_configs = NS(
            get=make(_Paged, "score_configs.get", configs), create=create_config
        )
        self.annotation_queues = NS(
            list_queues=make(_Paged, "annotation_queues.list_queues", queues),
            create_queue=create_queue,
            list_queue_items=make(_Paged, "annotation_queues.list_queue_items", items),
            create_queue_item=create_item,
        )
        self.observations = NS(get_many=make(_Cursor, "observations.get_many", observations))
        self.scores = NS(get_many=make(_Cursor, "scores.get_many", scores))

    def called(self, method):
        return [kw for m, kw in self.calls if m == method]

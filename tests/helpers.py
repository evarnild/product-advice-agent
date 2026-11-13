"""Test doubles shared across test modules."""

from advisor.models.base import Usage


class RecordingTracer:
    """A Tracer that records (kind, payload) events in order."""

    def __init__(self):
        self.events = []

    def begin(self, question):
        self.events.append(("begin", question))

    def check(self, stage, allowed, reason):
        self.events.append(("check", stage, allowed, reason))

    def generation(self, model: str, usage: Usage, text, tool_names):
        self.events.append(("generation", model, usage, text, list(tool_names)))

    def tool(self, name, arguments, results, error):
        self.events.append(("tool", name, arguments, results, error))

    def finish(self, answer):
        self.events.append(("finish", answer))

    def fail(self, error):
        self.events.append(("fail", error))

    @property
    def kinds(self):
        return [e[0] for e in self.events]


class RaisingTracer:
    """Every method raises; used to prove tracing can never change a run."""

    def __getattr__(self, name):
        def boom(*args, **kwargs):
            raise RuntimeError(f"tracer {name} failed")

        return boom

"""Configuration from environment variables, with a root `.env` loaded if present.

Credentials: keys are looked up by provider and returned to the caller; they
are never printed or logged here.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass

from dotenv import dotenv_values, find_dotenv

from advisor.models import PROVIDER_KEY_ENV

DEFAULT_PROVIDER = "anthropic"
DEFAULT_MODELS: dict[str, str] = {"anthropic": "claude-haiku-5-5"}


@dataclass(frozen=True)
class Settings:
    provider: str
    model: str
    env: Mapping[str, str]

    @property
    def key_variable(self) -> str | None:
        return PROVIDER_KEY_ENV.get(self.provider)

    def api_key(self) -> str | None:
        var = self.key_variable
        return (self.env.get(var) or None) if var else None


def load_env(environ: Mapping[str, str] | None = None) -> dict[str, str]:
    """Values from the nearest `.env` (searching up from the working directory),
    overridden by the real environment."""
    real = dict(os.environ if environ is None else environ)
    if environ is not None:
        return real  # explicit environment (tests): do not read any file
    path = find_dotenv(usecwd=True)
    from_file = {k: v for k, v in dotenv_values(path).items() if v is not None} if path else {}
    return {**from_file, **real}


def load_settings(env: Mapping[str, str]) -> Settings:
    provider = env.get("ADVISOR_MODEL_PROVIDER") or DEFAULT_PROVIDER
    model = env.get("ADVISOR_MODEL") or DEFAULT_MODELS.get(provider, "")
    return Settings(provider=provider, model=model, env=env)

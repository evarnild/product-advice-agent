"""Configuration from environment variables, with a root `.env` loaded if present.

Credentials: keys are looked up by provider and returned to the caller; they
are never printed or logged here.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from urllib.parse import urlsplit

from dotenv import dotenv_values, find_dotenv

from advisor.models import PROVIDER_KEY_ENV

# The default is local. An existing `.env` that pins ADVISOR_MODEL_PROVIDER
# (for example one copied from the old .env.example) keeps winning: the
# variable is doing its job, so it is documented and not overridden.
DEFAULT_PROVIDER = "ollama"
DEFAULT_MODELS: dict[str, str] = {"ollama": "qwen3:8b", "anthropic": "claude-haiku-5-5"}
# The advisor's own variable, not OLLAMA_HOST: the Ollama server reads
# OLLAMA_HOST as its bind address (often 0.0.0.0), which cannot be connected to.
DEFAULT_OLLAMA_URL = "http://localhost:11434"


class ConfigError(Exception):
    """A configuration value is invalid; the message names the variable."""


@dataclass(frozen=True)
class Settings:
    provider: str
    model: str
    env: Mapping[str, str]

    @property
    def api_key_variable(self) -> str | None:
        return PROVIDER_KEY_ENV.get(self.provider)

    def ollama_url(self) -> str:
        url = self.env.get("ADVISOR_OLLAMA_URL") or DEFAULT_OLLAMA_URL
        parts = urlsplit(url)
        if parts.scheme not in ("http", "https") or not parts.hostname:
            raise ConfigError("ADVISOR_OLLAMA_URL must be an http:// or https:// URL")
        return url

    def api_key(self) -> str | None:
        var = self.api_key_variable
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

"""Model providers behind the `ModelClient` protocol."""

from __future__ import annotations

from advisor.models.base import ModelClient

PROVIDER_KEY_ENV: dict[str, str] = {"anthropic": "ANTHROPIC_API_KEY"}
KNOWN_PROVIDERS: tuple[str, ...] = tuple(PROVIDER_KEY_ENV)


class UnknownProviderError(Exception):
    """The requested provider has no adapter."""


def make_client(provider: str, model: str, api_key: str) -> ModelClient:
    """Build the adapter for `provider`; raises UnknownProviderError, never calls the network."""
    if provider == "anthropic":
        from advisor.models.anthropic_model import AnthropicClient

        return AnthropicClient(api_key=api_key, model=model)
    raise UnknownProviderError(
        f"unknown model provider '{provider}'; known providers: {', '.join(KNOWN_PROVIDERS)}"
    )

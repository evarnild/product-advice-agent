"""Model providers behind the `ModelClient` protocol."""

from __future__ import annotations

from advisor.models.base import ModelClient

# Only providers that need a key appear here; a keyless provider (ollama) is
# known through KNOWN_PROVIDERS alone.
PROVIDER_KEY_ENV: dict[str, str] = {"anthropic": "ANTHROPIC_API_KEY"}
KNOWN_PROVIDERS: tuple[str, ...] = ("ollama", "anthropic")


class UnknownProviderError(Exception):
    """The requested provider has no adapter."""


def make_client(
    provider: str,
    model: str,
    *,
    api_key: str | None = None,
    base_url: str | None = None,
) -> ModelClient:
    """Build the adapter for `provider`; raises UnknownProviderError, never calls the network.

    Adapters are imported lazily so a run imports only its own provider's SDK.
    """
    if provider == "ollama":
        from advisor.models.ollama_model import DEFAULT_BASE_URL, OllamaClient

        return OllamaClient(model=model, base_url=base_url or DEFAULT_BASE_URL)
    if provider == "anthropic":
        from advisor.models.anthropic_model import AnthropicClient

        return AnthropicClient(api_key=api_key or "", model=model)
    raise UnknownProviderError(
        f"unknown model provider '{provider}'; known providers: {', '.join(KNOWN_PROVIDERS)}"
    )

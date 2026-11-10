import pytest

from advisor.config import DEFAULT_MODELS, ConfigError, load_env, load_settings


def test_defaults_are_local():
    s = load_settings({})
    assert (s.provider, s.model) == ("ollama", "qwen3:8b")
    assert s.api_key_variable is None
    assert s.api_key() is None
    assert load_settings({"ADVISOR_MODEL_PROVIDER": ""}).provider == "ollama"


def test_anthropic_still_selectable():
    s = load_settings({"ADVISOR_MODEL_PROVIDER": "anthropic", "ANTHROPIC_API_KEY": "k"})
    assert (s.provider, s.model) == ("anthropic", "claude-haiku-5-5")
    assert DEFAULT_MODELS["anthropic"] == "claude-haiku-5-5"
    assert s.api_key_variable == "ANTHROPIC_API_KEY"
    assert s.api_key() == "k"


def test_model_override():
    assert load_settings({"ADVISOR_MODEL": "m"}).model == "m"


def test_ollama_url_default_and_override():
    assert load_settings({}).ollama_url() == "http://localhost:11434"
    s = load_settings({"ADVISOR_OLLAMA_URL": "https://box:1/"})
    assert s.ollama_url() == "https://box:1/"


def test_ollama_host_is_not_read():
    assert load_settings({"OLLAMA_HOST": "0.0.0.0"}).ollama_url() == "http://localhost:11434"


@pytest.mark.parametrize("url", ["localhost:11434", "ftp://h", "box", "http://"])
def test_bad_ollama_url_names_the_variable(url):
    with pytest.raises(ConfigError, match="ADVISOR_OLLAMA_URL"):
        load_settings({"ADVISOR_OLLAMA_URL": url}).ollama_url()


def test_unknown_provider_has_no_key_variable():
    s = load_settings({"ADVISOR_MODEL_PROVIDER": "zzz"})
    assert s.api_key_variable is None and s.api_key() is None


def test_load_env_reads_dotenv_but_real_env_wins(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text("A=file\nB=file\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("B", "real")
    env = load_env()
    assert env["A"] == "file"
    assert env["B"] == "real"


def test_explicit_environment_reads_no_file(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text("A=file\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assert load_env({"X": "1"}) == {"X": "1"}

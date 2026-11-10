from advisor.config import DEFAULT_MODELS, load_env, load_settings


def test_defaults():
    s = load_settings({})
    assert (s.provider, s.model) == ("anthropic", DEFAULT_MODELS["anthropic"])
    assert DEFAULT_MODELS["anthropic"] == "claude-haiku-5-5"
    assert s.key_variable == "ANTHROPIC_API_KEY"
    assert s.api_key() is None


def test_overrides_and_key():
    s = load_settings({"ADVISOR_MODEL": "m", "ANTHROPIC_API_KEY": "k"})
    assert s.model == "m" and s.api_key() == "k"


def test_unknown_provider_has_no_key_variable():
    s = load_settings({"ADVISOR_MODEL_PROVIDER": "zzz"})
    assert s.key_variable is None and s.api_key() is None


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

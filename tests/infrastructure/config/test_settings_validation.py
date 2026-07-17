# tests/infrastructure/config/test_settings_validation.py

import pytest
from pydantic import ValidationError


def _make_settings(**overrides):
    """Instantiate Settings with env isolation."""
    from infrastructure.config.settings import Settings

    return Settings(**overrides)


class TestOpenAIApiKeyValidation:
    def test_raises_when_openai_api_key_missing(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        with pytest.raises(ValidationError, match="OPENAI_API_KEY"):
            _make_settings(openai_api_key="")

    def test_raises_when_openai_api_key_empty_string(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        with pytest.raises(ValidationError, match="OPENAI_API_KEY"):
            _make_settings(openai_api_key="")

    def test_valid_when_openai_api_key_set(self):
        s = _make_settings(openai_api_key="sk-test-key")
        assert s.openai_api_key == "sk-test-key"

    def test_no_hardcoded_api_key_default(self, monkeypatch):
        """CFG-04: Settings must not ship a real/hardcoded API key default."""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        with pytest.raises(ValidationError, match="OPENAI_API_KEY"):
            _make_settings(openai_api_key="")


class TestCorpusHfRepoConfig:
    def test_corpus_hf_repo_none_when_not_set(self, monkeypatch):
        monkeypatch.delenv("CORPUS_HF_REPO", raising=False)
        s = _make_settings(openai_api_key="sk-test-key", corpus_hf_repo=None)
        assert s.corpus_hf_repo is None

    def test_corpus_hf_repo_reads_from_env(self, monkeypatch):
        monkeypatch.setenv("CORPUS_HF_REPO", "owner/interview-corpus")
        s = _make_settings(openai_api_key="sk-test-key")
        assert s.corpus_hf_repo == "owner/interview-corpus"

    def test_corpus_hf_repo_can_be_set_directly(self):
        s = _make_settings(openai_api_key="sk-test-key", corpus_hf_repo="owner/repo")
        assert s.corpus_hf_repo == "owner/repo"


class TestHfTokenConfig:
    def test_hf_token_none_when_not_set(self, monkeypatch):
        monkeypatch.delenv("HF_TOKEN", raising=False)
        monkeypatch.delenv("HUGGINGFACE_TOKEN", raising=False)
        s = _make_settings(openai_api_key="sk-test-key", hf_token=None)
        assert s.hf_token is None

    def test_hf_token_reads_from_env(self, monkeypatch):
        monkeypatch.delenv("HUGGINGFACE_TOKEN", raising=False)
        monkeypatch.setenv("HF_TOKEN", "hf_abc123")
        s = _make_settings(openai_api_key="sk-test-key")
        assert s.hf_token == "hf_abc123"

    def test_hf_token_reads_huggingface_token_alias(self, monkeypatch):
        monkeypatch.delenv("HF_TOKEN", raising=False)
        monkeypatch.setenv("HUGGINGFACE_TOKEN", "hf_alias_token")
        s = _make_settings(openai_api_key="sk-test-key")
        assert s.hf_token == "hf_alias_token"


class TestEpic08RuntimeKnobs:
    """C1: Settings exposes EPIC-08 knobs (paths, timeouts, flags) via env/secrets."""

    def test_process_edge_defaults(self):
        s = _make_settings(openai_api_key="sk-test-key")
        assert s.server_host == "0.0.0.0"
        assert s.server_port == 7860

    def test_server_port_reads_port_env(self, monkeypatch):
        monkeypatch.delenv("SERVER_PORT", raising=False)
        monkeypatch.setenv("PORT", "8080")
        s = _make_settings(openai_api_key="sk-test-key")
        assert s.server_port == 8080

    def test_server_host_reads_from_env(self, monkeypatch):
        monkeypatch.setenv("SERVER_HOST", "127.0.0.1")
        s = _make_settings(openai_api_key="sk-test-key")
        assert s.server_host == "127.0.0.1"

    def test_sqlite_db_path_default_and_env(self, monkeypatch):
        s = _make_settings(openai_api_key="sk-test-key")
        assert s.sqlite_db_path == "data/questions.db"
        monkeypatch.setenv("SQLITE_DB_PATH", "/tmp/ops.db")
        s2 = _make_settings(openai_api_key="sk-test-key")
        assert s2.sqlite_db_path == "/tmp/ops.db"

    def test_logging_knobs_default_and_env(self, monkeypatch):
        s = _make_settings(openai_api_key="sk-test-key")
        assert s.log_level == "INFO"
        assert s.log_sink == "stdout"
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        monkeypatch.setenv("LOG_SINK", "stderr")
        s2 = _make_settings(openai_api_key="sk-test-key")
        assert s2.log_level == "DEBUG"
        assert s2.log_sink == "stderr"

    def test_health_probe_knobs_default_and_env(self, monkeypatch):
        s = _make_settings(openai_api_key="sk-test-key")
        assert s.health_probe_timeout_ms == 5000
        assert s.health_llm_probe_enabled is True
        assert s.health_db_probe_enabled is True
        assert s.health_sandbox_probe_enabled is True
        monkeypatch.setenv("HEALTH_PROBE_TIMEOUT_MS", "2500")
        monkeypatch.setenv("HEALTH_LLM_PROBE_ENABLED", "false")
        monkeypatch.setenv("HEALTH_DB_PROBE_ENABLED", "false")
        monkeypatch.setenv("HEALTH_SANDBOX_PROBE_ENABLED", "false")
        s2 = _make_settings(openai_api_key="sk-test-key")
        assert s2.health_probe_timeout_ms == 2500
        assert s2.health_llm_probe_enabled is False
        assert s2.health_db_probe_enabled is False
        assert s2.health_sandbox_probe_enabled is False

    def test_shutdown_drain_timeout_default_and_env(self, monkeypatch):
        s = _make_settings(openai_api_key="sk-test-key")
        assert s.shutdown_drain_timeout_s == 30
        monkeypatch.setenv("SHUTDOWN_DRAIN_TIMEOUT_S", "60")
        s2 = _make_settings(openai_api_key="sk-test-key")
        assert s2.shutdown_drain_timeout_s == 60


class TestSettingsIntegration:
    def test_full_valid_config(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-prod-key")
        monkeypatch.setenv("CORPUS_HF_REPO", "owner/repo")
        monkeypatch.setenv("HF_TOKEN", "hf_token")
        s = _make_settings(
            openai_api_key="sk-prod-key",
            corpus_hf_repo="owner/repo",
            hf_token="hf_token",
        )
        assert s.openai_api_key == "sk-prod-key"
        assert s.corpus_hf_repo == "owner/repo"
        assert s.hf_token == "hf_token"

    def test_defaults_are_sane(self):
        s = _make_settings(openai_api_key="sk-test-key")
        assert s.chat_model == "gpt-4o-mini"
        assert s.humanizer_enabled is True
        assert s.humanizer_follow_up_enabled is True
        assert s.llm_json_retry_attempts == 2
        assert s.sqlite_db_path == "data/questions.db"
        assert s.log_level == "INFO"
        assert s.health_probe_timeout_ms == 5000
        assert s.shutdown_drain_timeout_s == 30

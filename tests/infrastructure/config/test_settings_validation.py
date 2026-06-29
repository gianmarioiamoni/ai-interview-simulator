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
        s = _make_settings(openai_api_key="sk-test-key", hf_token=None)
        assert s.hf_token is None

    def test_hf_token_reads_from_env(self, monkeypatch):
        monkeypatch.setenv("HF_TOKEN", "hf_abc123")
        s = _make_settings(openai_api_key="sk-test-key")
        assert s.hf_token == "hf_abc123"


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

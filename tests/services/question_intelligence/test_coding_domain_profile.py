# tests/services/question_intelligence/test_coding_domain_profile.py
"""
Tests for CodingDomainProfile registry, CodingPromptBuilder domain blocks,
CodingQuestionGenerator factory, CodingQuestionPipeline _resolve_generator,
AITestGenerator / TestPromptBuilder domain hints, and backward compatibility.
"""

import pytest
from unittest.mock import MagicMock

from domain.contracts.interview.business_context import BusinessContext
from domain.contracts.user.role import RoleType
from domain.contracts.user.seniority_level import SeniorityLevel
from services.question_intelligence.coding_domain_profile import CodingDomainProfile
from services.question_intelligence.coding_domain_profile_registry import (
    CodingDomainProfileRegistry,
)
from services.question_intelligence.coding_prompt_builder import CodingPromptBuilder
from services.question_intelligence.coding_question_generator import CodingQuestionGenerator
from services.question_intelligence.pipelines.coding_question_pipeline import (
    CodingQuestionPipeline,
    CodingGeneratorFactory,
)
from services.question_intelligence.area_question_builder import (
    _build_coding_generator_factory,
)


# ── registry tests ─────────────────────────────────────────────────────────────


class TestCodingDomainProfileRegistry:
    def test_generic_returns_generic_profile(self):
        profile = CodingDomainProfileRegistry.get(BusinessContext.GENERIC)
        assert profile.context_key == BusinessContext.GENERIC

    def test_fintech_returns_fintech_profile(self):
        profile = CodingDomainProfileRegistry.get(BusinessContext.FINTECH)
        assert profile.context_key == BusinessContext.FINTECH

    def test_ecommerce_returns_ecommerce_profile(self):
        profile = CodingDomainProfileRegistry.get(BusinessContext.ECOMMERCE)
        assert profile.context_key == BusinessContext.ECOMMERCE

    def test_saas_returns_saas_profile(self):
        profile = CodingDomainProfileRegistry.get(BusinessContext.SAAS)
        assert profile.context_key == BusinessContext.SAAS

    def test_all_profiles_have_vocabulary_hints(self):
        for ctx in (BusinessContext.FINTECH, BusinessContext.ECOMMERCE, BusinessContext.SAAS):
            profile = CodingDomainProfileRegistry.get(ctx)
            assert len(profile.vocabulary_hint) > 0

    def test_all_profiles_have_scenario_anchor_pool(self):
        for ctx in (BusinessContext.FINTECH, BusinessContext.ECOMMERCE, BusinessContext.SAAS):
            profile = CodingDomainProfileRegistry.get(ctx)
            assert len(profile.scenario_anchor_pool) > 0

    def test_all_profiles_have_test_scenario_hints(self):
        for ctx in (BusinessContext.FINTECH, BusinessContext.ECOMMERCE, BusinessContext.SAAS):
            profile = CodingDomainProfileRegistry.get(ctx)
            assert len(profile.test_scenario_hints) > 0

    def test_fintech_vocabulary_contains_expected_terms(self):
        profile = CodingDomainProfileRegistry.get(BusinessContext.FINTECH)
        vocab_lower = [t.lower() for t in profile.vocabulary_hint]
        for term in ("transaction", "fraud", "balance"):
            assert term in vocab_lower

    def test_ecommerce_vocabulary_contains_expected_terms(self):
        profile = CodingDomainProfileRegistry.get(BusinessContext.ECOMMERCE)
        vocab_lower = [t.lower() for t in profile.vocabulary_hint]
        for term in ("inventory", "cart", "fulfillment"):
            assert term in vocab_lower

    def test_saas_vocabulary_contains_expected_terms(self):
        profile = CodingDomainProfileRegistry.get(BusinessContext.SAAS)
        vocab_lower = [t.lower() for t in profile.vocabulary_hint]
        for term in ("subscription", "tenant", "churn"):
            assert term in vocab_lower

    def test_profile_is_frozen(self):
        profile = CodingDomainProfileRegistry.get(BusinessContext.FINTECH)
        with pytest.raises((AttributeError, TypeError)):
            profile.context_key = BusinessContext.GENERIC  # type: ignore[misc]

    def test_generic_context_summary_is_none(self):
        profile = CodingDomainProfileRegistry.get(BusinessContext.GENERIC)
        assert profile.context_summary is None

    def test_non_generic_profiles_have_context_summary(self):
        for ctx in (BusinessContext.FINTECH, BusinessContext.ECOMMERCE, BusinessContext.SAAS):
            profile = CodingDomainProfileRegistry.get(ctx)
            assert profile.context_summary is not None
            assert len(profile.context_summary) > 0


# ── prompt builder block tests ────────────────────────────────────────────────


class TestCodingPromptBuilderDomainBlocks:
    def test_no_domain_framing_when_no_profile(self):
        builder = CodingPromptBuilder()
        prompt = builder.build_generation_prompt(role="backend", level="mid", n=1)
        assert "DOMAIN FRAMING" not in prompt

    def test_domain_framing_present_for_fintech(self):
        profile = CodingDomainProfileRegistry.get(BusinessContext.FINTECH)
        builder = CodingPromptBuilder(domain_profile=profile)
        prompt = builder.build_generation_prompt(role="backend", level="mid", n=1)
        assert "DOMAIN FRAMING" in prompt

    def test_domain_framing_contains_fintech_summary(self):
        profile = CodingDomainProfileRegistry.get(BusinessContext.FINTECH)
        builder = CodingPromptBuilder(domain_profile=profile)
        prompt = builder.build_generation_prompt(role="backend", level="mid", n=1)
        assert "financial" in prompt.lower() or "payment" in prompt.lower() or "fraud" in prompt.lower()

    def test_domain_framing_present_for_ecommerce(self):
        profile = CodingDomainProfileRegistry.get(BusinessContext.ECOMMERCE)
        builder = CodingPromptBuilder(domain_profile=profile)
        prompt = builder.build_generation_prompt(role="backend", level="mid", n=1)
        assert "DOMAIN FRAMING" in prompt

    def test_domain_framing_present_for_saas(self):
        profile = CodingDomainProfileRegistry.get(BusinessContext.SAAS)
        builder = CodingPromptBuilder(domain_profile=profile)
        prompt = builder.build_generation_prompt(role="backend", level="mid", n=1)
        assert "DOMAIN FRAMING" in prompt

    def test_no_vocabulary_block_when_no_profile(self):
        builder = CodingPromptBuilder()
        prompt = builder.build_generation_prompt(role="backend", level="mid", n=1)
        assert "DOMAIN VOCABULARY" not in prompt

    def test_vocabulary_block_present_for_fintech(self):
        profile = CodingDomainProfileRegistry.get(BusinessContext.FINTECH)
        builder = CodingPromptBuilder(domain_profile=profile)
        prompt = builder.build_generation_prompt(role="backend", level="mid", n=1)
        assert "DOMAIN VOCABULARY" in prompt
        assert "fraud" in prompt or "transaction" in prompt

    def test_vocabulary_block_present_for_ecommerce(self):
        profile = CodingDomainProfileRegistry.get(BusinessContext.ECOMMERCE)
        builder = CodingPromptBuilder(domain_profile=profile)
        prompt = builder.build_generation_prompt(role="backend", level="mid", n=1)
        assert "DOMAIN VOCABULARY" in prompt
        assert "inventory" in prompt or "fulfillment" in prompt

    def test_vocabulary_block_present_for_saas(self):
        profile = CodingDomainProfileRegistry.get(BusinessContext.SAAS)
        builder = CodingPromptBuilder(domain_profile=profile)
        prompt = builder.build_generation_prompt(role="backend", level="mid", n=1)
        assert "DOMAIN VOCABULARY" in prompt
        assert "subscription" in prompt or "tenant" in prompt

    def test_scenario_block_present_for_fintech(self):
        profile = CodingDomainProfileRegistry.get(BusinessContext.FINTECH)
        builder = CodingPromptBuilder(domain_profile=profile)
        prompt = builder.build_generation_prompt(role="backend", level="mid", n=1)
        assert "SCENARIO ANCHOR" in prompt

    def test_scenario_block_absent_for_generic_no_profile(self):
        builder = CodingPromptBuilder()
        prompt = builder.build_generation_prompt(role="backend", level="mid", n=1)
        assert "SCENARIO ANCHOR" not in prompt

    def test_domain_blocks_in_enrichment_prompt(self):
        profile = CodingDomainProfileRegistry.get(BusinessContext.FINTECH)
        builder = CodingPromptBuilder(domain_profile=profile)
        prompt = builder.build_enrichment_prompt(
            seed_prompt="Detect anomalous transactions", role="backend", level="mid"
        )
        assert "DOMAIN FRAMING" in prompt
        assert "DOMAIN VOCABULARY" in prompt
        assert "SCENARIO ANCHOR" in prompt

    def test_cd_block_label_renamed(self):
        builder = CodingPromptBuilder()
        prompt = builder.build_generation_prompt(
            role="backend", level="mid", n=1, company_description="A fintech startup."
        )
        assert "COMPANY DESCRIPTION" in prompt
        assert "BUSINESS CONTEXT" not in prompt


# ── feature flags ─────────────────────────────────────────────────────────────


class TestCodingDomainProfileFeatureFlags:
    def test_domain_framing_disabled_by_flag(self, monkeypatch):
        from infrastructure.config import settings as settings_module
        monkeypatch.setattr(settings_module.settings, "coding_domain_profile_enabled", False)
        profile = CodingDomainProfileRegistry.get(BusinessContext.FINTECH)
        builder = CodingPromptBuilder(domain_profile=profile)
        prompt = builder.build_generation_prompt(role="backend", level="mid", n=1)
        assert "DOMAIN FRAMING" not in prompt

    def test_vocabulary_disabled_by_flag(self, monkeypatch):
        from infrastructure.config import settings as settings_module
        monkeypatch.setattr(settings_module.settings, "coding_domain_vocabulary_enabled", False)
        profile = CodingDomainProfileRegistry.get(BusinessContext.FINTECH)
        builder = CodingPromptBuilder(domain_profile=profile)
        prompt = builder.build_generation_prompt(role="backend", level="mid", n=1)
        assert "DOMAIN VOCABULARY" not in prompt

    def test_scenario_disabled_by_flag(self, monkeypatch):
        from infrastructure.config import settings as settings_module
        monkeypatch.setattr(settings_module.settings, "coding_scenario_anchor_enabled", False)
        profile = CodingDomainProfileRegistry.get(BusinessContext.FINTECH)
        builder = CodingPromptBuilder(domain_profile=profile)
        prompt = builder.build_generation_prompt(role="backend", level="mid", n=1)
        assert "SCENARIO ANCHOR" not in prompt


# ── generator factory tests ───────────────────────────────────────────────────


class TestCodingGeneratorFactory:
    def test_generic_returns_default_generator(self):
        default_gen = MagicMock(spec=CodingQuestionGenerator)
        factory = _build_coding_generator_factory(MagicMock(), default_gen)
        assert factory(BusinessContext.GENERIC) is default_gen

    def test_fintech_returns_different_generator(self):
        default_gen = CodingQuestionGenerator(MagicMock())
        factory = _build_coding_generator_factory(MagicMock(), default_gen)
        fintech_gen = factory(BusinessContext.FINTECH)
        assert fintech_gen is not default_gen

    def test_factory_caches_generators(self):
        default_gen = CodingQuestionGenerator(MagicMock())
        factory = _build_coding_generator_factory(MagicMock(), default_gen)
        gen1 = factory(BusinessContext.FINTECH)
        gen2 = factory(BusinessContext.FINTECH)
        assert gen1 is gen2

    def test_ecommerce_returns_ecommerce_generator(self):
        default_gen = MagicMock(spec=CodingQuestionGenerator)
        factory = _build_coding_generator_factory(MagicMock(), default_gen)
        ecom_gen = factory(BusinessContext.ECOMMERCE)
        assert ecom_gen is not default_gen

    def test_saas_returns_saas_generator(self):
        default_gen = MagicMock(spec=CodingQuestionGenerator)
        factory = _build_coding_generator_factory(MagicMock(), default_gen)
        saas_gen = factory(BusinessContext.SAAS)
        assert saas_gen is not default_gen

    def test_fintech_generator_has_fintech_profile(self):
        default_gen = CodingQuestionGenerator(MagicMock())
        factory = _build_coding_generator_factory(MagicMock(), default_gen)
        fintech_gen = factory(BusinessContext.FINTECH)
        profile = fintech_gen._prompt_builder._domain_profile
        assert profile is not None
        assert profile.context_key == BusinessContext.FINTECH

    def test_generic_generator_has_no_profile(self):
        llm = MagicMock()
        default_gen = CodingQuestionGenerator(llm)
        factory = _build_coding_generator_factory(llm, default_gen)
        generic_gen = factory(BusinessContext.GENERIC)
        assert generic_gen is default_gen


# ── pipeline _resolve_generator tests ────────────────────────────────────────


class TestCodingPipelineResolveGenerator:
    def _make_pipeline(self, default_gen, factory=None):
        return CodingQuestionPipeline(
            retrieval_service=MagicMock(),
            coding_generator=default_gen,
            generator_factory=factory,
        )

    def test_no_factory_returns_default(self):
        default_gen = MagicMock(spec=CodingQuestionGenerator)
        pipeline = self._make_pipeline(default_gen)
        assert pipeline._resolve_generator(BusinessContext.FINTECH) is default_gen

    def test_factory_returns_context_specific(self):
        default_gen = MagicMock(spec=CodingQuestionGenerator)
        fintech_gen = MagicMock(spec=CodingQuestionGenerator)
        factory = lambda ctx: fintech_gen if ctx == BusinessContext.FINTECH else default_gen
        pipeline = self._make_pipeline(default_gen, factory)
        assert pipeline._resolve_generator(BusinessContext.FINTECH) is fintech_gen
        assert pipeline._resolve_generator(BusinessContext.GENERIC) is default_gen

    def test_none_context_returns_default(self):
        default_gen = MagicMock(spec=CodingQuestionGenerator)
        factory = lambda ctx: MagicMock()
        pipeline = self._make_pipeline(default_gen, factory)
        assert pipeline._resolve_generator(None) is default_gen

    def test_generate_with_retry_calls_resolved_generator(self):
        default_gen = MagicMock(spec=CodingQuestionGenerator)
        fintech_gen = MagicMock(spec=CodingQuestionGenerator)
        fintech_gen.generate.return_value = []
        factory = lambda ctx: fintech_gen if ctx == BusinessContext.FINTECH else default_gen

        pipeline = self._make_pipeline(default_gen, factory)
        pipeline._generate_with_retry(
            role=RoleType.BACKEND_ENGINEER,
            level=SeniorityLevel.MID,
            n=1,
            business_context=BusinessContext.FINTECH,
        )
        fintech_gen.generate.assert_called()
        default_gen.generate.assert_not_called()

    def test_enrich_item_calls_resolved_generator(self):
        from domain.contracts.question.question_bank_item import QuestionBankItem
        from domain.contracts.question.question_provenance import QuestionProvenance

        default_gen = MagicMock(spec=CodingQuestionGenerator)
        fintech_gen = MagicMock(spec=CodingQuestionGenerator)
        fintech_gen.enrich_from_prompt.return_value = None
        factory = lambda ctx: fintech_gen if ctx == BusinessContext.FINTECH else default_gen

        pipeline = self._make_pipeline(default_gen, factory)
        item = MagicMock(spec=QuestionBankItem)
        item.text = "Implement a fraud detection algorithm"
        item.difficulty = None
        item.id = "item-1"
        provenance = MagicMock(spec=QuestionProvenance)

        from domain.contracts.interview.interview_area import InterviewArea
        pipeline._enrich_item(
            item=item,
            role=RoleType.BACKEND_ENGINEER,
            level=SeniorityLevel.MID,
            area=InterviewArea.TECH_CODING,
            provenance=provenance,
            theme_guidance=None,
            business_context=BusinessContext.FINTECH,
        )
        fintech_gen.enrich_from_prompt.assert_called_once()
        default_gen.enrich_from_prompt.assert_not_called()


# ── TestPromptBuilder domain hints tests ─────────────────────────────────────


class TestTestPromptBuilderDomainHints:
    def _make_spec(self):
        from domain.contracts.execution.coding_spec import CodingSpec
        return CodingSpec(type="function", entrypoint="solve", parameters=["nums"])

    def test_no_domain_hints_block_without_profile(self):
        from app.ai.test_generation.test_prompt_builder import TestPromptBuilder
        builder = TestPromptBuilder()
        spec = self._make_spec()
        prompt = builder.build(problem="Find max subarray sum.", spec=spec, num_tests=3)
        assert "DOMAIN TEST HINTS" not in prompt

    def test_domain_hints_present_for_fintech_profile(self):
        from app.ai.test_generation.test_prompt_builder import TestPromptBuilder
        profile = CodingDomainProfileRegistry.get(BusinessContext.FINTECH)
        builder = TestPromptBuilder()
        spec = self._make_spec()
        prompt = builder.build(problem="Detect fraudulent transactions.", spec=spec, num_tests=3, domain_profile=profile)
        assert "DOMAIN TEST HINTS" in prompt

    def test_domain_hints_contain_fintech_edge_cases(self):
        from app.ai.test_generation.test_prompt_builder import TestPromptBuilder
        profile = CodingDomainProfileRegistry.get(BusinessContext.FINTECH)
        builder = TestPromptBuilder()
        spec = self._make_spec()
        prompt = builder.build(problem="Balance reconciliation.", spec=spec, num_tests=3, domain_profile=profile)
        assert any(hint in prompt for hint in profile.test_scenario_hints)

    def test_domain_hints_present_for_saas_profile(self):
        from app.ai.test_generation.test_prompt_builder import TestPromptBuilder
        profile = CodingDomainProfileRegistry.get(BusinessContext.SAAS)
        builder = TestPromptBuilder()
        spec = self._make_spec()
        prompt = builder.build(problem="Calculate MRR.", spec=spec, num_tests=3, domain_profile=profile)
        assert "DOMAIN TEST HINTS" in prompt

    def test_domain_hints_absent_for_generic_profile(self):
        from app.ai.test_generation.test_prompt_builder import TestPromptBuilder
        profile = CodingDomainProfileRegistry.get(BusinessContext.GENERIC)
        builder = TestPromptBuilder()
        spec = self._make_spec()
        # GENERIC has test_scenario_hints — block should still appear
        prompt = builder.build(problem="Sort a list.", spec=spec, num_tests=3, domain_profile=profile)
        assert "DOMAIN TEST HINTS" in prompt


# ── backward compatibility tests ──────────────────────────────────────────────


class TestBackwardCompatibility:
    def test_coding_prompt_builder_no_args_still_works(self):
        builder = CodingPromptBuilder()
        prompt = builder.build_generation_prompt(role="backend", level="mid", n=1)
        assert "Generate" in prompt
        assert "Python" in prompt

    def test_coding_question_generator_no_profile_still_works(self):
        gen = CodingQuestionGenerator(MagicMock())
        assert gen._prompt_builder._domain_profile is None

    def test_coding_pipeline_no_factory_still_works(self):
        default_gen = MagicMock(spec=CodingQuestionGenerator)
        pipeline = CodingQuestionPipeline(
            retrieval_service=MagicMock(),
            coding_generator=default_gen,
        )
        assert pipeline._generator_factory is None
        assert pipeline._resolve_generator(BusinessContext.FINTECH) is default_gen

    def test_existing_blocks_unaffected_by_profile(self):
        builder = CodingPromptBuilder()
        prompt = builder.build_generation_prompt(
            role="backend",
            level="senior",
            n=2,
            theme_guidance="recursion",
            job_description="Build APIs",
        )
        assert "recursion" in prompt
        assert "Build APIs" in prompt

    def test_ai_test_generator_without_profile_unchanged(self):
        from app.ai.test_generation.ai_test_generator import AITestGenerator
        from domain.contracts.question.question import Question, QuestionType, QuestionDifficulty
        from domain.contracts.execution.coding_spec import CodingSpec
        from domain.contracts.interview.interview_area import InterviewArea

        llm = MagicMock()
        response = MagicMock()
        response.content = '[{"args": [1], "expected": 1}]'
        llm.invoke.return_value = response

        gen = AITestGenerator(llm)
        question = MagicMock(spec=Question)
        question.coding_spec = CodingSpec(type="function", entrypoint="f", parameters=["x"])
        question.prompt = "Write a function f(x)."
        question.id = "test-q"

        gen._cache.get_tests = MagicMock(return_value=None)
        gen._cache.store_tests = MagicMock()
        gen._diversity_filter.filter = lambda tests, n: tests[:n]

        result = gen.generate_tests(question, num_tests=1)
        assert isinstance(result, list)

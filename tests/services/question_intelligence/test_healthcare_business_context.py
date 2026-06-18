# tests/services/question_intelligence/test_healthcare_business_context.py
"""
Classifier tests for HEALTHCARE BusinessContext.
Covers: keyword classification, collision safety, pipeline routing,
coding profile injection, and schema registry.
"""

import pytest
from domain.contracts.interview.business_context import BusinessContext


# ── Classifier accuracy ───────────────────────────────────────────────────────


class TestHealthcareClassifier:
    def _classify(self, cd: str) -> BusinessContext:
        return BusinessContext.from_company_description(cd)

    def test_pure_healthcare_ehr(self):
        assert self._classify(
            "A healthcare company building an EHR system for patients and physicians."
        ) == BusinessContext.HEALTHCARE

    def test_hospital_network(self):
        assert self._classify(
            "A hospital network managing patient records and clinical workflows."
        ) == BusinessContext.HEALTHCARE

    def test_pharmacy_platform(self):
        assert self._classify(
            "A pharmacy management platform with prescription tracking and patient care."
        ) == BusinessContext.HEALTHCARE

    def test_telehealth_only(self):
        assert self._classify(
            "A telehealth company enabling remote patient consultations and digital care delivery."
        ) == BusinessContext.HEALTHCARE

    def test_generic_clinical(self):
        assert self._classify(
            "A clinical platform for doctors and nurses."
        ) == BusinessContext.HEALTHCARE

    def test_hipaa_fhir_mention(self):
        assert self._classify(
            "A HIPAA-compliant platform for EHR data using FHIR standards."
        ) == BusinessContext.HEALTHCARE

    def test_empty_description_returns_generic(self):
        assert self._classify(None) == BusinessContext.GENERIC
        assert self._classify("") == BusinessContext.GENERIC

    def test_below_threshold_returns_generic(self):
        assert self._classify("A healthcare startup.") == BusinessContext.GENERIC

    def test_fintech_dominant_over_healthcare(self):
        result = self._classify(
            "A medical insurance and financial services company providing fraud detection "
            "and healthcare payment processing and financial transactions."
        )
        assert result == BusinessContext.FINTECH

    def test_saas_dominant_over_healthcare_when_saas_wins(self):
        result = self._classify(
            "A mental health SaaS platform with subscription plans, multi-tenant architecture, "
            "billing, cloud usage analytics, and workspace management."
        )
        assert result == BusinessContext.SAAS

    def test_healthcare_wins_when_dominant(self):
        assert self._classify(
            "A healthcare company providing clinical EHR tools for patients, physicians, "
            "diagnoses, prescriptions, and clinical workflows."
        ) == BusinessContext.HEALTHCARE

    def test_pure_saas_not_misclassified(self):
        assert self._classify(
            "A SaaS platform with multi-tenant subscriptions, billing, usage analytics, "
            "and workspace management."
        ) == BusinessContext.SAAS

    def test_pure_fintech_not_misclassified(self):
        assert self._classify(
            "A fintech company for payment processing, fraud detection, and financial transactions."
        ) == BusinessContext.FINTECH

    def test_pure_ecommerce_not_misclassified(self):
        assert self._classify(
            "An ecommerce marketplace with orders, products, inventory, and fulfillment."
        ) == BusinessContext.ECOMMERCE


# ── No keyword collision with existing sets ───────────────────────────────────


class TestHealthcareKeywordCollisions:
    def test_no_collision_with_fintech(self):
        from domain.contracts.interview.business_context import (
            _HEALTHCARE_KEYWORDS, _FINTECH_KEYWORDS,
        )
        assert len(_HEALTHCARE_KEYWORDS & _FINTECH_KEYWORDS) == 0

    def test_no_collision_with_ecommerce(self):
        from domain.contracts.interview.business_context import (
            _HEALTHCARE_KEYWORDS, _ECOMMERCE_KEYWORDS,
        )
        assert len(_HEALTHCARE_KEYWORDS & _ECOMMERCE_KEYWORDS) == 0

    def test_no_collision_with_saas(self):
        from domain.contracts.interview.business_context import (
            _HEALTHCARE_KEYWORDS, _SAAS_KEYWORDS,
        )
        assert len(_HEALTHCARE_KEYWORDS & _SAAS_KEYWORDS) == 0

    def test_healthcare_keywords_non_empty(self):
        from domain.contracts.interview.business_context import _HEALTHCARE_KEYWORDS
        assert len(_HEALTHCARE_KEYWORDS) >= 10


# ── SQL pipeline routing ──────────────────────────────────────────────────────


class TestHealthcareSQLPipelineRouting:
    def test_healthcare_in_metadata_only_set(self):
        from services.question_intelligence.pipelines.sql_question_pipeline import (
            _BUSINESS_CONTEXT_METADATA_ONLY,
        )
        assert BusinessContext.HEALTHCARE in _BUSINESS_CONTEXT_METADATA_ONLY

    def test_healthcare_schema_in_registry(self):
        from services.sql_engine.schema_registry import SchemaRegistry
        defn = SchemaRegistry.get(BusinessContext.HEALTHCARE)
        assert defn.context_key == BusinessContext.HEALTHCARE
        assert "patients" in defn.schema_sql
        assert "employees" not in defn.schema_sql

    def test_healthcare_seed_data_populated(self):
        from services.sql_engine.schema_registry import SchemaRegistry
        defn = SchemaRegistry.get(BusinessContext.HEALTHCARE)
        assert "INSERT INTO patients" in defn.seed_sql
        assert "INSERT INTO prescriptions" in defn.seed_sql


# ── Coding domain profile routing ────────────────────────────────────────────


class TestHealthcareCodingProfile:
    def test_healthcare_coding_profile_in_registry(self):
        from services.question_intelligence.coding_domain_profile_registry import (
            CodingDomainProfileRegistry,
        )
        profile = CodingDomainProfileRegistry.get(BusinessContext.HEALTHCARE)
        assert profile.context_key == BusinessContext.HEALTHCARE

    def test_healthcare_coding_profile_has_clinical_vocabulary(self):
        from services.question_intelligence.coding_domain_profile_registry import (
            CodingDomainProfileRegistry,
        )
        profile = CodingDomainProfileRegistry.get(BusinessContext.HEALTHCARE)
        vocab_lower = [t.lower() for t in profile.vocabulary_hint]
        for term in ("patient", "diagnosis", "prescription"):
            assert term in vocab_lower

    def test_healthcare_coding_profile_has_clinical_anchors(self):
        from services.question_intelligence.coding_domain_profile_registry import (
            CodingDomainProfileRegistry,
        )
        profile = CodingDomainProfileRegistry.get(BusinessContext.HEALTHCARE)
        pool_text = " ".join(profile.scenario_anchor_pool).lower()
        assert "appointment" in pool_text or "diagnosis" in pool_text

    def test_healthcare_prompt_contains_domain_framing(self):
        from services.question_intelligence.coding_domain_profile_registry import (
            CodingDomainProfileRegistry,
        )
        from services.question_intelligence.coding_prompt_builder import CodingPromptBuilder
        profile = CodingDomainProfileRegistry.get(BusinessContext.HEALTHCARE)
        builder = CodingPromptBuilder(domain_profile=profile)
        prompt = builder.build_generation_prompt(role="backend", level="mid", n=1)
        assert "DOMAIN FRAMING" in prompt
        assert "DOMAIN VOCABULARY" in prompt
        assert "SCENARIO ANCHOR" in prompt

    def test_healthcare_factory_returns_healthcare_generator(self):
        from unittest.mock import MagicMock
        from services.question_intelligence.coding_question_generator import CodingQuestionGenerator
        from services.question_intelligence.area_question_builder import (
            _build_coding_generator_factory,
        )
        default_gen = CodingQuestionGenerator(MagicMock())
        factory = _build_coding_generator_factory(MagicMock(), default_gen)
        hc_gen = factory(BusinessContext.HEALTHCARE)
        assert hc_gen is not default_gen
        assert hc_gen._prompt_builder._domain_profile.context_key == BusinessContext.HEALTHCARE

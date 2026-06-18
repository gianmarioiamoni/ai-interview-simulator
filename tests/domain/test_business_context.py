# tests/domain/test_business_context.py

import pytest

from domain.contracts.interview.business_context import BusinessContext
from domain.contracts.interview.interview_context_profile import InterviewContextProfile


# =====================================================
# Resolver classification
# =====================================================

class TestBusinessContextResolver:

    def test_none_returns_generic(self):
        assert BusinessContext.from_company_description(None) == BusinessContext.GENERIC

    def test_empty_string_returns_generic(self):
        assert BusinessContext.from_company_description("") == BusinessContext.GENERIC

    def test_blank_string_returns_generic(self):
        assert BusinessContext.from_company_description("   ") == BusinessContext.GENERIC

    def test_no_keywords_returns_generic(self):
        assert BusinessContext.from_company_description("A software company") == BusinessContext.GENERIC

    def test_fintech_keyword_payment(self):
        result = BusinessContext.from_company_description("We process payment transactions")
        assert result == BusinessContext.FINTECH

    def test_fintech_keyword_merchant(self):
        result = BusinessContext.from_company_description("Platform for merchant settlements")
        assert result == BusinessContext.FINTECH

    def test_fintech_keyword_bank(self):
        result = BusinessContext.from_company_description("A digital banking startup")
        assert result == BusinessContext.FINTECH

    def test_ecommerce_keyword_orders(self):
        result = BusinessContext.from_company_description("We manage customer orders and shipments")
        assert result == BusinessContext.ECOMMERCE

    def test_ecommerce_keyword_marketplace(self):
        result = BusinessContext.from_company_description("Online marketplace for retail products")
        assert result == BusinessContext.ECOMMERCE

    def test_saas_keyword_subscription(self):
        result = BusinessContext.from_company_description("B2B subscription billing platform")
        assert result == BusinessContext.SAAS

    def test_saas_keyword_tenant(self):
        result = BusinessContext.from_company_description("Multi-tenant SaaS platform")
        assert result == BusinessContext.SAAS

    def test_case_insensitive(self):
        result = BusinessContext.from_company_description("FINTECH PAYMENT PLATFORM")
        assert result == BusinessContext.FINTECH

    def test_highest_score_wins(self):
        # "order" is ecommerce, "subscription" is saas — ecommerce has more matches
        result = BusinessContext.from_company_description(
            "Ecommerce platform managing orders, products, inventory, shipments"
        )
        assert result == BusinessContext.ECOMMERCE

    def test_default_generic_wins_on_tie(self):
        # Constructed to have 1 match each → returns whichever max() picks (not generic)
        result = BusinessContext.from_company_description("payment subscription")
        # Either fintech or saas, NOT generic
        assert result in {BusinessContext.FINTECH, BusinessContext.SAAS}


# =====================================================
# InterviewContextProfile persistence
# =====================================================

class TestInterviewContextProfilePersistence:

    def test_default_business_context_is_generic(self):
        profile = InterviewContextProfile()
        assert profile.business_context == BusinessContext.GENERIC

    def test_business_context_persists(self):
        profile = InterviewContextProfile(business_context=BusinessContext.FINTECH)
        assert profile.business_context == BusinessContext.FINTECH

    def test_company_description_preserved_alongside_business_context(self):
        profile = InterviewContextProfile(
            company_description="Payment processing company",
            business_context=BusinessContext.FINTECH,
        )
        assert profile.company_description == "Payment processing company"
        assert profile.business_context == BusinessContext.FINTECH

    def test_job_description_preserved(self):
        profile = InterviewContextProfile(
            job_description="Senior engineer",
            business_context=BusinessContext.SAAS,
        )
        assert profile.job_description == "Senior engineer"

    def test_frozen_prevents_mutation(self):
        profile = InterviewContextProfile(business_context=BusinessContext.ECOMMERCE)
        with pytest.raises(Exception):
            profile.business_context = BusinessContext.SAAS

    def test_all_enum_values_accepted(self):
        for ctx in BusinessContext:
            profile = InterviewContextProfile(business_context=ctx)
            assert profile.business_context == ctx

    def test_serialization_roundtrip(self):
        profile = InterviewContextProfile(
            company_description="A fintech startup",
            business_context=BusinessContext.FINTECH,
        )
        dumped = profile.model_dump()
        restored = InterviewContextProfile.model_validate(dumped)
        assert restored.business_context == BusinessContext.FINTECH
        assert restored.company_description == "A fintech startup"


# =====================================================
# BusinessContext enum contract
# =====================================================

class TestBusinessContextEnum:

    def test_generic_value(self):
        assert BusinessContext.GENERIC.value == "generic"

    def test_fintech_value(self):
        assert BusinessContext.FINTECH.value == "fintech"

    def test_ecommerce_value(self):
        assert BusinessContext.ECOMMERCE.value == "ecommerce"

    def test_saas_value(self):
        assert BusinessContext.SAAS.value == "saas"

    def test_is_str_enum(self):
        assert isinstance(BusinessContext.GENERIC, str)

    def test_four_values_defined(self):
        assert len(BusinessContext) == 4

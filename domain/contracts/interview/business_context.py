# domain/contracts/interview/business_context.py

from __future__ import annotations

from enum import Enum

from domain.contracts.interview.business_context_constants import (
    BUSINESS_CONTEXT_MIN_KEYWORD_SCORE,
)


# Module-level keyword sets — single source of truth for classification vocabulary.

_FINTECH_KEYWORDS: frozenset[str] = frozenset({
    "fintech", "bank", "banking", "payment", "payments", "transaction",
    "transactions", "merchant", "merchants", "settlement", "settlements",
    "ledger", "fraud", "lending", "credit", "debit", "wallet", "finance",
    "financial", "insurance", "trading", "brokerage", "exchange",
})

_ECOMMERCE_KEYWORDS: frozenset[str] = frozenset({
    "ecommerce", "e-commerce", "shop", "shopping", "retail", "store",
    "marketplace", "order", "orders", "product", "products", "inventory",
    "shipment", "shipping", "delivery", "cart", "checkout", "catalog",
    "fulfilment", "fulfillment", "warehouse",
})

_SAAS_KEYWORDS: frozenset[str] = frozenset({
    "saas", "software as a service", "subscription", "subscriptions",
    "tenant", "tenants", "multi-tenant", "multitenant", "plan", "plans",
    "usage", "billing", "b2b", "platform", "cloud", "workspace", "tier",
})

_HEALTHCARE_KEYWORDS: frozenset[str] = frozenset({
    "healthcare", "hospital", "patient", "patients", "clinical",
    "medical", "physician", "doctor", "nurse", "nursing",
    "ehr", "emr", "fhir", "hl7", "hipaa", "diagnosis", "diagnoses",
    "prescription", "prescriptions", "pharmacy", "laboratory",
    "telemedicine", "telehealth", "clinic", "appointment", "appointments",
    "radiology", "pathology", "health record", "electronic health",
    "patient care", "clinical workflow", "care coordination",
    "health information",
})

# Explicit tie-breaking priority (lower index = higher priority on equal score).
# Documented: FINTECH > ECOMMERCE > SAAS > HEALTHCARE when scores are equal.
_PRIORITY: list[str] = ["fintech", "ecommerce", "saas", "healthcare"]


class BusinessContext(str, Enum):
    GENERIC = "generic"
    FINTECH = "fintech"
    ECOMMERCE = "ecommerce"
    SAAS = "saas"
    HEALTHCARE = "healthcare"

    @classmethod
    def from_company_description(cls, company_description: str | None) -> "BusinessContext":
        if not company_description or not company_description.strip():
            return cls.GENERIC

        text = company_description.lower()
        threshold = BUSINESS_CONTEXT_MIN_KEYWORD_SCORE

        scores: dict[str, int] = {
            "fintech": sum(1 for kw in _FINTECH_KEYWORDS if kw in text),
            "ecommerce": sum(1 for kw in _ECOMMERCE_KEYWORDS if kw in text),
            "saas": sum(1 for kw in _SAAS_KEYWORDS if kw in text),
            "healthcare": sum(1 for kw in _HEALTHCARE_KEYWORDS if kw in text),
        }

        max_score = max(scores.values())

        if max_score < threshold:
            return cls.GENERIC

        # Explicit tie-breaking: FINTECH > ECOMMERCE > SAAS
        for context_value in _PRIORITY:
            if scores[context_value] == max_score:
                return cls(context_value)

        return cls.GENERIC

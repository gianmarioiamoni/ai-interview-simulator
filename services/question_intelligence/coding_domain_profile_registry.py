# services/question_intelligence/coding_domain_profile_registry.py

from domain.contracts.interview.business_context import BusinessContext
from services.question_intelligence.coding_domain_profile import CodingDomainProfile

_GENERIC_PROFILE = CodingDomainProfile(
    context_key=BusinessContext.GENERIC,
    context_summary=None,
    vocabulary_hint=(
        "algorithm", "recursion", "graph", "tree", "cache",
        "traversal", "dynamic programming", "greedy", "backtracking",
    ),
    entity_hint=(
        "list", "matrix", "string", "node", "queue", "stack", "heap",
    ),
    scenario_anchor_pool=(
        "search", "sort", "transform", "validate", "parse",
        "count", "group", "merge", "split",
    ),
    test_scenario_hints=(
        "empty input", "single element", "large n", "duplicates", "boundary values",
    ),
)

_FINTECH_PROFILE = CodingDomainProfile(
    context_key=BusinessContext.FINTECH,
    context_summary=(
        "Frame the problem in a financial services context: "
        "payments, transactions, accounts, fraud detection, or risk."
    ),
    vocabulary_hint=(
        "transaction", "balance", "ledger", "fraud", "settlement",
        "reconciliation", "chargeback", "payment", "transfer", "portfolio",
    ),
    entity_hint=(
        "account", "transaction", "payment", "wallet", "portfolio",
        "merchant", "customer", "currency",
    ),
    scenario_anchor_pool=(
        "fraud detection", "balance reconciliation", "risk scoring",
        "rate limiting", "fee calculation", "transaction aggregation",
        "account merge", "currency conversion",
    ),
    test_scenario_hints=(
        "zero balance", "overdraft", "duplicate transaction",
        "large transaction volume", "negative amount", "concurrent updates",
    ),
)

_ECOMMERCE_PROFILE = CodingDomainProfile(
    context_key=BusinessContext.ECOMMERCE,
    context_summary=(
        "Frame the problem in an e-commerce context: "
        "products, orders, inventory, pricing, or fulfillment."
    ),
    vocabulary_hint=(
        "inventory", "fulfillment", "pricing", "discount", "cart",
        "shipment", "returns", "catalog", "sku", "warehouse",
    ),
    entity_hint=(
        "product", "cart", "order", "warehouse", "customer",
        "category", "supplier", "review",
    ),
    scenario_anchor_pool=(
        "stock management", "price calculation", "order routing",
        "returns processing", "discount application", "inventory restock",
        "cart validation", "search ranking",
    ),
    test_scenario_hints=(
        "out-of-stock", "zero quantity", "negative discount",
        "empty cart", "large catalogue", "concurrent order",
    ),
)

_SAAS_PROFILE = CodingDomainProfile(
    context_key=BusinessContext.SAAS,
    context_summary=(
        "Frame the problem in a SaaS context: "
        "subscriptions, tenants, usage tracking, billing, or feature access."
    ),
    vocabulary_hint=(
        "subscription", "tenant", "billing", "quota", "churn",
        "retention", "MRR", "ARR", "feature", "usage", "tier",
    ),
    entity_hint=(
        "tenant", "user", "plan", "feature", "subscription",
        "seat", "workspace", "event",
    ),
    scenario_anchor_pool=(
        "usage tracking", "billing calculation", "quota enforcement",
        "feature gating", "churn prediction", "seat management",
        "plan upgrade", "trial expiry",
    ),
    test_scenario_hints=(
        "expired plan", "zero usage", "unlimited quota",
        "concurrent tenants", "plan downgrade", "single seat",
    ),
)

_HEALTHCARE_PROFILE = CodingDomainProfile(
    context_key=BusinessContext.HEALTHCARE,
    context_summary=(
        "Frame the problem in a healthcare context: "
        "patients, appointments, diagnoses, prescriptions, providers, or clinical workflows."
    ),
    vocabulary_hint=(
        "patient", "diagnosis", "prescription", "physician", "nurse",
        "appointment", "encounter", "ehr", "fhir", "hipaa",
        "laboratory", "referral",
    ),
    entity_hint=(
        "patient", "provider", "appointment", "diagnosis", "prescription",
        "lab_result", "encounter", "care_plan",
    ),
    scenario_anchor_pool=(
        "appointment scheduling", "diagnosis validation",
        "prescription interaction check", "lab result aggregation",
        "referral routing", "care coordination",
        "clinical workflow automation", "patient triage",
    ),
    test_scenario_hints=(
        "duplicate diagnosis code", "expired prescription",
        "no-show appointment", "missing patient record",
        "concurrent encounter update", "empty lab results",
    ),
)

_REGISTRY: dict[BusinessContext, CodingDomainProfile] = {
    BusinessContext.GENERIC: _GENERIC_PROFILE,
    BusinessContext.FINTECH: _FINTECH_PROFILE,
    BusinessContext.ECOMMERCE: _ECOMMERCE_PROFILE,
    BusinessContext.SAAS: _SAAS_PROFILE,
    BusinessContext.HEALTHCARE: _HEALTHCARE_PROFILE,
}


class CodingDomainProfileRegistry:
    @staticmethod
    def get(business_context: BusinessContext) -> CodingDomainProfile:
        return _REGISTRY.get(business_context, _GENERIC_PROFILE)

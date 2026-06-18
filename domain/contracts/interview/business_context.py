# domain/contracts/interview/business_context.py

from __future__ import annotations

from enum import Enum


class BusinessContext(str, Enum):
    GENERIC = "generic"
    FINTECH = "fintech"
    ECOMMERCE = "ecommerce"
    SAAS = "saas"

    @classmethod
    def from_company_description(cls, company_description: str | None) -> "BusinessContext":
        if not company_description or not company_description.strip():
            return cls.GENERIC

        text = company_description.lower()

        fintech_keywords = {
            "fintech", "bank", "banking", "payment", "payments", "transaction",
            "transactions", "merchant", "merchants", "settlement", "settlements",
            "ledger", "fraud", "lending", "credit", "debit", "wallet", "finance",
            "financial", "insurance", "trading", "brokerage", "exchange",
        }
        ecommerce_keywords = {
            "ecommerce", "e-commerce", "shop", "shopping", "retail", "store",
            "marketplace", "order", "orders", "product", "products", "inventory",
            "shipment", "shipping", "delivery", "cart", "checkout", "catalog",
            "fulfilment", "fulfillment", "warehouse",
        }
        saas_keywords = {
            "saas", "software as a service", "subscription", "subscriptions",
            "tenant", "tenants", "multi-tenant", "multitenant", "plan", "plans",
            "usage", "billing", "b2b", "platform", "cloud", "workspace", "tier",
        }

        scores: dict[BusinessContext, int] = {
            cls.FINTECH: sum(1 for kw in fintech_keywords if kw in text),
            cls.ECOMMERCE: sum(1 for kw in ecommerce_keywords if kw in text),
            cls.SAAS: sum(1 for kw in saas_keywords if kw in text),
        }

        best = max(scores, key=lambda k: scores[k])

        if scores[best] == 0:
            return cls.GENERIC

        return best

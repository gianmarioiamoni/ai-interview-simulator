# scripts/question_intelligence/audit_company_description_strength.py
#
# Company Description Strength Audit
# role=backend_engineer, seniority=senior
# 7 scenarios x 3 areas x 30 questions = 630 questions

from __future__ import annotations

import json
import re
import sys
import uuid
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.interview.interview_type import InterviewType
from domain.contracts.user.role import RoleType
from domain.contracts.user.seniority_level import SeniorityLevel
from infrastructure.llm.llm_adapter import DefaultLLMAdapter
from services.question_intelligence.area_question_builder import AreaQuestionBuilder
from services.question_intelligence.coding_question_generator import CodingQuestionGenerator
from services.question_intelligence.question_generator import QuestionGenerator
from services.question_intelligence.question_retrieval_service import QuestionRetrievalService
from services.question_intelligence.question_vector_store import QuestionVectorStore
from services.question_intelligence.sql_question_generator import SQLQuestionGenerator
from infrastructure.vector_store.chroma_question_store import ChromaQuestionStore

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "scripts/question_intelligence/output"
QUESTIONS_PER_SCENARIO_AREA = 30
ROLE = RoleType.BACKEND_ENGINEER
LEVEL = SeniorityLevel.SENIOR
INTERVIEW_TYPE = InterviewType.TECHNICAL
TARGET_AREAS = [
    InterviewArea.TECH_DATABASE,
    InterviewArea.TECH_CODING,
    InterviewArea.TECH_CASE_STUDY,
]

SCENARIOS: dict[str, str | None] = {
    "none": None,
    "fintech": (
        "We are a fintech company providing real-time payment processing, fraud detection, "
        "transaction ledger management, and regulatory compliance (PCI-DSS, AML). "
        "Our systems handle millions of financial transactions per day with strict auditability, "
        "low latency, and high availability requirements. Core entities: payment, transaction, "
        "account, ledger, fraud_score, compliance_event, settlement."
    ),
    "saas": (
        "We are a B2B SaaS company offering a cloud-based project management and collaboration platform. "
        "Multi-tenant architecture with subscription billing, usage metering, and feature flags. "
        "Key entities: tenant, subscription, workspace, user, feature_flag, usage_event, invoice, "
        "webhook. We operate globally with strict SLA requirements and zero-downtime deployments."
    ),
    "ecommerce": (
        "We run a large-scale e-commerce marketplace connecting buyers and sellers globally. "
        "Core operations: product catalog management, inventory tracking, order fulfillment, "
        "payment processing, seller performance, and recommendation engine. "
        "Key entities: product, SKU, inventory, order, cart, seller, buyer, review, promotion, shipment."
    ),
    "telecom": (
        "We are a telecommunications provider operating mobile and fixed-line networks. "
        "Systems manage network provisioning, subscriber lifecycle, billing, roaming, "
        "and network quality monitoring. Key entities: subscriber, sim_card, data_plan, "
        "call_record, billing_cycle, network_node, roaming_event, service_outage."
    ),
    "healthcare": (
        "We build healthcare data infrastructure for hospitals and clinics. "
        "Systems manage patient records, clinical workflows, medical device integration, "
        "and HIPAA-compliant data exchange. Key entities: patient, encounter, diagnosis, "
        "prescription, lab_result, medical_device, insurance_claim, audit_log."
    ),
    "manufacturing": (
        "We are an industrial manufacturing company with smart factory operations. "
        "Systems track production lines, equipment maintenance, supply chain, quality control, "
        "and IoT sensor data. Key entities: production_order, machine, sensor_reading, "
        "maintenance_schedule, defect_report, supplier, bill_of_materials, shift."
    ),
}

# =========================================================
# Domain vocabulary per scenario for vocabulary analysis
# =========================================================

DOMAIN_VOCAB: dict[str, list[str]] = {
    "none": [],
    "fintech": [
        "payment", "transaction", "ledger", "fraud", "fraud_score", "compliance",
        "pci", "aml", "settlement", "account", "audit", "regulatory", "fintech",
        "financial", "banking", "transfer", "wallet", "kyc", "risk", "clearing",
    ],
    "saas": [
        "tenant", "subscription", "workspace", "feature_flag", "usage_event",
        "invoice", "webhook", "multi-tenant", "billing", "metering", "saas",
        "onboarding", "churn", "mrr", "arr", "tier", "plan", "rate_limit",
    ],
    "ecommerce": [
        "product", "sku", "inventory", "order", "cart", "seller", "buyer",
        "review", "promotion", "shipment", "marketplace", "catalog", "checkout",
        "fulfillment", "recommendation", "wishlist", "coupon", "stock",
    ],
    "telecom": [
        "subscriber", "sim_card", "data_plan", "call_record", "billing_cycle",
        "network_node", "roaming", "outage", "provisioning", "telecom",
        "mobile", "carrier", "bandwidth", "sms", "voip", "handset",
    ],
    "healthcare": [
        "patient", "encounter", "diagnosis", "prescription", "lab_result",
        "medical_device", "insurance_claim", "hipaa", "ehr", "clinical",
        "healthcare", "physician", "medication", "icd", "fhir", "hl7",
    ],
    "manufacturing": [
        "production_order", "machine", "sensor_reading", "maintenance_schedule",
        "defect_report", "supplier", "bill_of_materials", "shift", "iot",
        "manufacturing", "assembly", "quality_control", "scada", "plc", "erp",
    ],
}

# Generic entities to track for entity shift
GENERIC_ENTITIES = ["employee", "department", "salary", "project", "user", "manager"]

BUSINESS_ENTITY_MAP: dict[str, list[str]] = {
    "fintech": ["payment", "transaction", "account", "ledger", "settlement", "fraud_score"],
    "saas": ["tenant", "subscription", "workspace", "invoice", "usage_event", "feature_flag"],
    "ecommerce": ["product", "sku", "order", "seller", "buyer", "shipment"],
    "telecom": ["subscriber", "sim_card", "data_plan", "call_record", "network_node"],
    "healthcare": ["patient", "encounter", "diagnosis", "prescription", "lab_result"],
    "manufacturing": ["production_order", "machine", "sensor_reading", "defect_report", "supplier"],
}


# =========================================================
# Helpers
# =========================================================


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9_]+", text.lower())


def _token_set(text: str) -> set[str]:
    return set(_tokenize(text))


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    union = a | b
    return round(len(a & b) / len(union), 4) if union else 0.0


def _lexical_divergence(texts_a: list[str], texts_b: list[str]) -> float:
    """1 - mean pairwise Jaccard similarity between two question sets."""
    tokens_a = [_token_set(t) for t in texts_a]
    tokens_b = [_token_set(t) for t in texts_b]
    pairs = [(a, b) for a in tokens_a for b in tokens_b]
    if not pairs:
        return 0.0
    mean_sim = sum(_jaccard(a, b) for a, b in pairs) / len(pairs)
    return round(1.0 - mean_sim, 4)


def _vocab_coverage(texts: list[str], scenario_key: str) -> dict[str, float]:
    vocab = DOMAIN_VOCAB.get(scenario_key, [])
    all_tokens = _tokenize(" ".join(texts))
    total = len(all_tokens)
    if total == 0:
        return {"generic_pct": 0.0, "business_specific_pct": 0.0, "unique_business_entities_pct": 0.0}

    business_hits = sum(1 for t in all_tokens if t in vocab)
    generic_hits = sum(1 for t in all_tokens if t in GENERIC_ENTITIES)
    unique_entities = set(t for t in all_tokens if t in BUSINESS_ENTITY_MAP.get(scenario_key, []))

    return {
        "generic_pct": round(generic_hits / total * 100, 2),
        "business_specific_pct": round(business_hits / total * 100, 2),
        "unique_business_entities_pct": round(len(unique_entities) / max(len(BUSINESS_ENTITY_MAP.get(scenario_key, [1])), 1) * 100, 2),
    }


def _entity_shift(texts: list[str], scenario_key: str) -> dict[str, Any]:
    all_tokens = _tokenize(" ".join(texts))
    token_counts = Counter(all_tokens)

    generic_present = {e: token_counts[e] for e in GENERIC_ENTITIES if token_counts[e] > 0}
    business_entities = BUSINESS_ENTITY_MAP.get(scenario_key, [])
    business_present = {e: token_counts[e] for e in business_entities if token_counts[e] > 0}

    return {
        "generic_entities_found": generic_present,
        "business_entities_found": business_present,
        "generic_count": sum(generic_present.values()),
        "business_count": sum(business_present.values()),
        "replacement_ratio": round(
            sum(business_present.values()) / max(sum(generic_present.values()) + sum(business_present.values()), 1),
            3,
        ),
    }


def _difficulty_stats(difficulties: list[int]) -> dict[str, float]:
    if not difficulties:
        return {}
    return {
        "mean": round(sum(difficulties) / len(difficulties), 2),
        "min": min(difficulties),
        "max": max(difficulties),
    }


def _business_context_preservation(texts: list[str], scenario_key: str) -> dict[str, Any]:
    """Count unique business terms, business entities, and business scenario markers."""
    vocab = DOMAIN_VOCAB.get(scenario_key, [])
    if not vocab:
        return {"term_hits": 0, "entity_hits": 0, "scenario_mentions": 0, "score": 0.0}

    all_tokens = _tokenize(" ".join(texts))
    token_counts = Counter(all_tokens)

    term_hits = sum(1 for v in vocab if token_counts[v] > 0)
    entity_hits = len([e for e in BUSINESS_ENTITY_MAP.get(scenario_key, []) if token_counts[e] > 0])
    scenario_mentions = sum(token_counts[v] for v in vocab)

    score = round(term_hits / max(len(vocab), 1) * 100, 2)
    return {
        "term_hits": term_hits,
        "entity_hits": entity_hits,
        "scenario_mentions": scenario_mentions,
        "score": score,
    }


# =========================================================
# Generation
# =========================================================


def _build_area_builder(llm: Any) -> AreaQuestionBuilder:
    chroma_store = ChromaQuestionStore()
    vector_store = QuestionVectorStore(chroma_store)
    retrieval_service = QuestionRetrievalService(vector_store)
    generator = QuestionGenerator(llm)
    coding_generator = CodingQuestionGenerator(llm)
    sql_generator = SQLQuestionGenerator(llm)
    return AreaQuestionBuilder(
        retrieval_service=retrieval_service,
        generator=generator,
        coding_generator=coding_generator,
        sql_generator=sql_generator,
    )


def _generate_questions_for_area(
    builder: AreaQuestionBuilder,
    area: InterviewArea,
    company_description: str | None,
    n: int,
) -> list[str]:
    """
    Generate n questions in as few calls as possible.
    We call build() with questions_per_area=n once; if the result is short
    (e.g. SQL pipeline retries exhausted), we top up in batches of 5.
    """
    try:
        questions, _ = builder.build(
            role=ROLE,
            level=LEVEL,
            interview_type=INTERVIEW_TYPE,
            area=area,
            questions_per_area=n,
            company_description=company_description,
        )
        texts = [q.prompt for q in questions]
    except Exception as exc:
        print(f"  [WARN] generation error for {area.value}: {exc}", flush=True)
        texts = []

    # Top-up if short
    while len(texts) < n:
        remaining = n - len(texts)
        ask = min(5, remaining)
        try:
            questions, _ = builder.build(
                role=ROLE,
                level=LEVEL,
                interview_type=INTERVIEW_TYPE,
                area=area,
                questions_per_area=ask,
                company_description=company_description,
            )
            texts.extend(q.prompt for q in questions)
        except Exception as exc:
            print(f"  [WARN] top-up error for {area.value}: {exc}", flush=True)
            break

    return texts[:n]


def _collect_scenario_data(
    builder: AreaQuestionBuilder,
    scenario_key: str,
    company_description: str | None,
    n_per_area: int,
) -> dict[str, Any]:
    data: dict[str, Any] = {}
    for area in TARGET_AREAS:
        print(f"  [{scenario_key}] {area.value} ...", flush=True)
        texts = _generate_questions_for_area(builder, area, company_description, n_per_area)
        data[area.value] = texts
    return data


# =========================================================
# Metrics
# =========================================================


def _compute_scenario_metrics(
    scenario_key: str,
    area_texts: dict[str, list[str]],
) -> dict[str, Any]:
    all_texts = [t for texts in area_texts.values() for t in texts]
    metrics: dict[str, Any] = {
        "total_questions": len(all_texts),
        "vocab_coverage": _vocab_coverage(all_texts, scenario_key),
        "entity_shift": _entity_shift(all_texts, scenario_key),
        "context_preservation": _business_context_preservation(all_texts, scenario_key),
        "by_area": {},
    }
    for area_key, texts in area_texts.items():
        metrics["by_area"][area_key] = {
            "count": len(texts),
        }
    return metrics


def _compute_pairwise_divergence(
    all_scenarios: dict[str, dict[str, list[str]]],
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    scenario_keys = list(all_scenarios.keys())

    for ka, kb in combinations(scenario_keys, 2):
        texts_a_all = [t for ts in all_scenarios[ka].values() for t in ts]
        texts_b_all = [t for ts in all_scenarios[kb].values() for t in ts]

        lex_div = _lexical_divergence(texts_a_all, texts_b_all)

        vocab_a = set(DOMAIN_VOCAB.get(ka, []))
        vocab_b = set(DOMAIN_VOCAB.get(kb, []))
        tokens_a = _token_set(" ".join(texts_a_all))
        tokens_b = _token_set(" ".join(texts_b_all))
        biz_a = tokens_a & vocab_a
        biz_b = tokens_b & vocab_b
        biz_context_div = round(1.0 - _jaccard(biz_a, biz_b), 4)

        results.append({
            "pair": f"{ka} vs {kb}",
            "lexical_divergence": lex_div,
            "business_context_divergence": biz_context_div,
        })

    return results


def _company_influence_score(
    baseline_texts: list[str],
    scenario_texts: list[str],
    scenario_key: str,
) -> float:
    """
    Estimate how much of the content shift is attributable to company description.
    = (business vocab density in scenario) / (1 + business vocab density in baseline)
    scaled to 0-100.
    """
    vocab = DOMAIN_VOCAB.get(scenario_key, [])
    if not vocab:
        return 0.0

    def density(texts: list[str], v: list[str]) -> float:
        tokens = _tokenize(" ".join(texts))
        if not tokens:
            return 0.0
        return sum(1 for t in tokens if t in v) / len(tokens)

    d_scenario = density(scenario_texts, vocab)
    d_baseline = density(baseline_texts, vocab)
    influence = round((d_scenario / max(d_scenario + d_baseline, 1e-9)) * 100, 2)
    return influence


# =========================================================
# Main
# =========================================================


def main() -> None:
    load_dotenv()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    llm = DefaultLLMAdapter()
    builder = _build_area_builder(llm)

    print(f"Starting Company Description Strength Audit", flush=True)
    print(f"Scenarios: {list(SCENARIOS.keys())}", flush=True)
    print(f"Areas: {[a.value for a in TARGET_AREAS]}", flush=True)
    print(f"Questions per scenario-area: {QUESTIONS_PER_SCENARIO_AREA}", flush=True)
    print(f"Total expected: {len(SCENARIOS) * len(TARGET_AREAS) * QUESTIONS_PER_SCENARIO_AREA}", flush=True)
    print("", flush=True)

    raw_data: dict[str, dict[str, list[str]]] = {}

    for scenario_key, company_description in SCENARIOS.items():
        print(f"[scenario={scenario_key}]", flush=True)
        raw_data[scenario_key] = _collect_scenario_data(
            builder=builder,
            scenario_key=scenario_key,
            company_description=company_description,
            n_per_area=QUESTIONS_PER_SCENARIO_AREA,
        )

    print("\nComputing metrics...", flush=True)

    per_scenario_metrics: dict[str, Any] = {}
    for scenario_key, area_texts in raw_data.items():
        per_scenario_metrics[scenario_key] = _compute_scenario_metrics(scenario_key, area_texts)

    pairwise = _compute_pairwise_divergence(raw_data)

    baseline_texts = [t for ts in raw_data["none"].values() for t in ts]
    influence_scores: dict[str, float] = {}
    for scenario_key in SCENARIOS:
        if scenario_key == "none":
            influence_scores["none"] = 0.0
            continue
        scenario_texts = [t for ts in raw_data[scenario_key].values() for t in ts]
        influence_scores[scenario_key] = _company_influence_score(baseline_texts, scenario_texts, scenario_key)

    report = {
        "audit": "Company Description Strength Audit",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "config": {
            "role": ROLE.value,
            "seniority": LEVEL.value,
            "interview_type": INTERVIEW_TYPE.value,
            "areas": [a.value for a in TARGET_AREAS],
            "questions_per_scenario_area": QUESTIONS_PER_SCENARIO_AREA,
            "scenarios": list(SCENARIOS.keys()),
        },
        "per_scenario_metrics": per_scenario_metrics,
        "pairwise_divergence": pairwise,
        "company_influence_scores": influence_scores,
        "raw_questions": raw_data,
    }

    output_path = OUTPUT_DIR / "company_description_strength_audit.json"
    output_path.write_text(json.dumps(report, indent=2))
    print(f"\nFull report saved: {output_path}", flush=True)

    _print_summary(per_scenario_metrics, pairwise, influence_scores)


def _print_summary(
    per_scenario: dict[str, Any],
    pairwise: list[dict[str, Any]],
    influence: dict[str, float],
) -> None:
    print("\n" + "=" * 70, flush=True)
    print("COMPANY DESCRIPTION STRENGTH AUDIT — SUMMARY", flush=True)
    print("=" * 70, flush=True)

    print("\n[1] Business Context Preservation Score (% of domain vocab covered)")
    for sc, m in per_scenario.items():
        cp = m["context_preservation"]
        print(f"  {sc:15s}: {cp['score']:6.2f}%  (term_hits={cp['term_hits']}, entity_hits={cp['entity_hits']}, mentions={cp['scenario_mentions']})")

    print("\n[2] Vocabulary Coverage")
    print(f"  {'scenario':15s}  {'generic%':>10s}  {'biz_specific%':>15s}  {'entity_cov%':>12s}")
    for sc, m in per_scenario.items():
        vc = m["vocab_coverage"]
        print(f"  {sc:15s}  {vc['generic_pct']:>10.2f}  {vc['business_specific_pct']:>15.2f}  {vc['unique_business_entities_pct']:>12.2f}")

    print("\n[3] Entity Shift (generic → business)")
    print(f"  {'scenario':15s}  {'generic_cnt':>12s}  {'business_cnt':>13s}  {'replacement_ratio':>18s}")
    for sc, m in per_scenario.items():
        es = m["entity_shift"]
        print(f"  {sc:15s}  {es['generic_count']:>12d}  {es['business_count']:>13d}  {es['replacement_ratio']:>18.3f}")

    print("\n[4] Company Influence Score (0=no influence, 100=full influence)")
    for sc, score in influence.items():
        print(f"  {sc:15s}: {score:.2f}")

    print("\n[5] Top Pairwise Divergence (lexical)")
    sorted_pairs = sorted(pairwise, key=lambda x: x["lexical_divergence"], reverse=True)
    for p in sorted_pairs[:5]:
        print(f"  {p['pair']:30s}  lex={p['lexical_divergence']:.4f}  biz_ctx={p['business_context_divergence']:.4f}")

    print("\n[6] Lowest divergence (most generic/overlap)")
    for p in sorted_pairs[-3:]:
        print(f"  {p['pair']:30s}  lex={p['lexical_divergence']:.4f}  biz_ctx={p['business_context_divergence']:.4f}")

    inf_sorted = sorted(
        [(k, v) for k, v in influence.items() if k != "none"],
        key=lambda x: x[1],
        reverse=True,
    )
    if inf_sorted:
        print(f"\n[7] Strongest company type: {inf_sorted[0][0]} (influence={inf_sorted[0][1]:.2f})")
        print(f"    Weakest  company type: {inf_sorted[-1][0]} (influence={inf_sorted[-1][1]:.2f})")


if __name__ == "__main__":
    main()

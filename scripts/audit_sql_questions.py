#!/usr/bin/env python3
"""
SQL Question Generation Audit Script
Generates 20 questions per context (FINTECH, ECOMMERCE, SAAS) using real LLM
and audits structural quality.
"""

import sys
import os
import re
import json
from collections import Counter
from typing import Any

# Add project root to path
sys.path.insert(0, "/Users/gianmarioiamoni/PROGRAMMAZIONE/Projects/ai-interview-simulator")

# Load .env
from dotenv import load_dotenv
load_dotenv("/Users/gianmarioiamoni/PROGRAMMAZIONE/Projects/ai-interview-simulator/.env")

from infrastructure.config.settings import settings
from domain.contracts.interview.business_context import BusinessContext
from domain.contracts.user.role import RoleType
from domain.contracts.user.seniority_level import SeniorityLevel
from services.sql_engine.schema_registry import SchemaRegistry
from services.question_intelligence.sql_question_generator import SQLQuestionGenerator

# ──────────────────────────────────────────────────────────────────────────────
# LLM Initialization
# ──────────────────────────────────────────────────────────────────────────────

USE_REAL_LLM = bool(settings.openai_api_key)

if USE_REAL_LLM:
    print(f"[INFO] OpenAI API key found. Using real LLM: {settings.chat_model}")
    from infrastructure.llm.llm_adapter import DefaultLLMAdapter
    llm = DefaultLLMAdapter()
else:
    print("[INFO] No OpenAI API key. Using mock LLM.")

    # Mock responses for each context
    MOCK_RESPONSES = {
        "FINTECH": [
            {
                "prompt": f"Write a SQL query to find customers whose total transaction amount exceeds $10,000 in a single month. Use accounts and transactions tables.",
                "reference_query": "SELECT c.name, SUM(t.amount) as total FROM customers c JOIN accounts a ON c.id=a.customer_id JOIN transactions t ON a.id=t.account_id WHERE t.direction='debit' GROUP BY c.id, strftime('%Y-%m', t.transaction_date) HAVING SUM(t.amount) > 10000;",
                "test_cases": [{"expected_query": "SELECT c.name, SUM(t.amount) as total FROM customers c JOIN accounts a ON c.id=a.customer_id JOIN transactions t ON a.id=t.account_id WHERE t.direction='debit' GROUP BY c.id, strftime('%Y-%m', t.transaction_date) HAVING SUM(t.amount) > 10000;", "ordered": False}]
            },
            {
                "prompt": f"Find all accounts with a balance below $500 and at least one credit transaction in the last 30 days.",
                "reference_query": "SELECT DISTINCT a.id, a.balance FROM accounts a JOIN transactions t ON a.id=t.account_id WHERE a.balance < 500 AND t.direction='credit' AND t.transaction_date >= date('now', '-30 days');",
                "test_cases": [{"expected_query": "SELECT DISTINCT a.id, a.balance FROM accounts a JOIN transactions t ON a.id=t.account_id WHERE a.balance < 500 AND t.direction='credit' AND t.transaction_date >= date('now', '-30 days');", "ordered": False}]
            },
        ] * 10,
        "ECOMMERCE": [
            {
                "prompt": f"Find customers who placed orders in both January and February 2024. Return customer name and total orders.",
                "reference_query": "SELECT c.name, COUNT(*) as total_orders FROM customers c JOIN orders o ON c.id=o.customer_id WHERE strftime('%Y-%m', o.order_date) IN ('2024-01', '2024-02') GROUP BY c.id HAVING COUNT(DISTINCT strftime('%Y-%m', o.order_date)) = 2;",
                "test_cases": [{"expected_query": "SELECT c.name, COUNT(*) as total_orders FROM customers c JOIN orders o ON c.id=o.customer_id WHERE strftime('%Y-%m', o.order_date) IN ('2024-01', '2024-02') GROUP BY c.id HAVING COUNT(DISTINCT strftime('%Y-%m', o.order_date)) = 2;", "ordered": False}]
            },
            {
                "prompt": f"List products with low inventory (stock_quantity < 20) that have been ordered at least 3 times.",
                "reference_query": "SELECT p.name, p.stock_quantity, COUNT(oi.id) as order_count FROM products p JOIN order_items oi ON p.id=oi.product_id WHERE p.stock_quantity < 20 GROUP BY p.id HAVING COUNT(oi.id) >= 3;",
                "test_cases": [{"expected_query": "SELECT p.name, p.stock_quantity, COUNT(oi.id) as order_count FROM products p JOIN order_items oi ON p.id=oi.product_id WHERE p.stock_quantity < 20 GROUP BY p.id HAVING COUNT(oi.id) >= 3;", "ordered": False}]
            },
        ] * 10,
        "SAAS": [
            {
                "prompt": f"Find tenants whose total usage_events units exceed their subscription plan's max_usage_units in January 2024.",
                "reference_query": "SELECT t.name, SUM(ue.units) as used, p.max_usage_units FROM tenants t JOIN subscriptions s ON t.id=s.tenant_id JOIN plans p ON s.plan_id=p.id JOIN usage_events ue ON t.id=ue.tenant_id WHERE strftime('%Y-%m', ue.event_date)='2024-01' GROUP BY t.id HAVING SUM(ue.units) > p.max_usage_units;",
                "test_cases": [{"expected_query": "SELECT t.name, SUM(ue.units) as used, p.max_usage_units FROM tenants t JOIN subscriptions s ON t.id=s.tenant_id JOIN plans p ON s.plan_id=p.id JOIN usage_events ue ON t.id=ue.tenant_id WHERE strftime('%Y-%m', ue.event_date)='2024-01' GROUP BY t.id HAVING SUM(ue.units) > p.max_usage_units;", "ordered": False}]
            },
            {
                "prompt": f"List all tenants on the Starter plan with active subscriptions whose billing would exceed $50 based on actual usage.",
                "reference_query": "SELECT t.name, s.status, p.price_monthly FROM tenants t JOIN subscriptions s ON t.id=s.tenant_id JOIN plans p ON s.plan_id=p.id WHERE p.name='Starter' AND s.status='active';",
                "test_cases": [{"expected_query": "SELECT t.name, s.status, p.price_monthly FROM tenants t JOIN subscriptions s ON t.id=s.tenant_id JOIN plans p ON s.plan_id=p.id WHERE p.name='Starter' AND s.status='active';", "ordered": False}]
            },
        ] * 10,
    }

    class MockLLMResponse:
        def __init__(self, content: str):
            self.content = content

    class MockLLM:
        def __init__(self, context_name: str):
            self._context = context_name
            self._call_count = 0

        def invoke(self, prompt: str) -> MockLLMResponse:
            items = MOCK_RESPONSES.get(self._context, MOCK_RESPONSES["FINTECH"])
            item = items[self._call_count % len(items)]
            self._call_count += 1
            # Return as JSON array expected by the parser
            response = json.dumps([{
                "prompt": item["prompt"],
                "reference_query": item["reference_query"],
                "test_cases": item["test_cases"]
            }])
            return MockLLMResponse(content=response)

        def invoke_json(self, prompt: str, schema):
            return schema()

# ──────────────────────────────────────────────────────────────────────────────
# Context Configuration
# ──────────────────────────────────────────────────────────────────────────────

CONTEXTS = [
    BusinessContext.FINTECH,
    BusinessContext.ECOMMERCE,
    BusinessContext.SAAS,
]

CONTEXT_TABLES = {
    BusinessContext.FINTECH: {"customers", "accounts", "transactions", "portfolios"},
    BusinessContext.ECOMMERCE: {"customers", "categories", "products", "orders", "order_items"},
    BusinessContext.SAAS: {"tenants", "plans", "subscriptions", "users", "usage_events"},
}

CONTEXT_VOCAB = {
    BusinessContext.FINTECH: ["account", "transaction", "payment", "balance", "portfolio"],
    BusinessContext.ECOMMERCE: ["order", "product", "customer", "cart", "inventory"],
    BusinessContext.SAAS: ["tenant", "subscription", "plan", "usage", "billing"],
}

HR_TERMS = ["employees", "departments", "salary", "projects"]

N_QUESTIONS = 20

# ──────────────────────────────────────────────────────────────────────────────
# Generation
# ──────────────────────────────────────────────────────────────────────────────

print("\n" + "="*70)
print("SQL QUESTION GENERATION AUDIT")
print("="*70)

all_results = {}

for ctx in CONTEXTS:
    ctx_name = ctx.value.upper()
    print(f"\n[GEN] Generating {N_QUESTIONS} questions for {ctx_name}...")

    schema_def = SchemaRegistry.get(ctx)

    if USE_REAL_LLM:
        current_llm = llm
    else:
        current_llm = MockLLM(ctx_name)

    generator = SQLQuestionGenerator(llm=current_llm, schema_definition=schema_def)

    questions = []
    errors = 0

    # Generate in batches of 5 to stay within LLM context
    batch_size = 5
    batches = N_QUESTIONS // batch_size

    for batch in range(batches):
        try:
            batch_questions = generator.generate(
                role=RoleType.DATA_ENGINEER,
                level=SeniorityLevel.MID,
                n=batch_size,
            )
            questions.extend(batch_questions)
            print(f"  Batch {batch+1}/{batches}: got {len(batch_questions)} questions")
        except Exception as e:
            print(f"  Batch {batch+1}/{batches}: ERROR - {e}")
            errors += 1

    all_results[ctx_name] = {"questions": questions, "errors": errors, "schema_def": schema_def}
    print(f"  Total generated: {len(questions)} | Errors: {errors}")

# ──────────────────────────────────────────────────────────────────────────────
# Audit
# ──────────────────────────────────────────────────────────────────────────────

print("\n" + "="*70)
print("AUDIT RESULTS")
print("="*70)

summary_rows = []
all_entities = {}

for ctx_name, data in all_results.items():
    ctx_enum = BusinessContext[ctx_name]
    questions = data["questions"]
    schema_def = data["schema_def"]

    valid_tables = CONTEXT_TABLES[ctx_enum]
    vocab_terms = CONTEXT_VOCAB[ctx_enum]
    hr_terms = HR_TERMS

    schema_aligned = 0
    vocab_scores = []
    hr_leakage_count = 0
    db_schema_present = 0
    db_seed_present = 0
    prompts = []
    entity_counter = Counter()

    for q in questions:
        prompt_lower = q.prompt.lower()
        schema_lower = (q.db_schema or "").lower()
        seed_lower = (q.db_seed_data or "").lower()

        # a. Schema alignment: check only valid table names appear
        mentioned_tables = set()
        for t in valid_tables:
            if t in prompt_lower:
                mentioned_tables.add(t)
        # Check for invalid tables from other schemas
        all_tables = set()
        for v in CONTEXT_TABLES.values():
            all_tables.update(v)
        invalid_mentions = [t for t in (all_tables - valid_tables) if t in prompt_lower]
        if not invalid_mentions:
            schema_aligned += 1
        entity_counter.update(mentioned_tables)

        # b. Business vocabulary score
        vocab_count = sum(1 for term in vocab_terms if term in prompt_lower)
        vocab_scores.append(vocab_count)

        # c. HR leakage
        hr_found = [t for t in hr_terms if t in prompt_lower or t in schema_lower]
        if hr_found:
            hr_leakage_count += 1

        # d. db_schema present
        if q.db_schema and len(q.db_schema.strip()) > 20:
            db_schema_present += 1

        # e. db_seed_data present
        if q.db_seed_data and len(q.db_seed_data.strip()) > 20:
            db_seed_present += 1

        prompts.append(q.prompt.strip().lower())

    # f. Duplicate prompts
    total = len(questions)
    unique_prompts = len(set(prompts))
    duplicate_count = total - unique_prompts
    duplicate_pct = (duplicate_count / total * 100) if total > 0 else 0

    avg_vocab = sum(vocab_scores) / len(vocab_scores) if vocab_scores else 0

    # Quality score (0-100)
    schema_score = (schema_aligned / total * 100) if total > 0 else 0
    vocab_score_norm = min(avg_vocab / len(vocab_terms) * 100, 100)
    hr_penalty = (hr_leakage_count / total * 100) if total > 0 else 0
    dup_penalty = duplicate_pct
    db_schema_score = (db_schema_present / total * 100) if total > 0 else 0
    db_seed_score = (db_seed_present / total * 100) if total > 0 else 0

    quality = (
        schema_score * 0.30
        + vocab_score_norm * 0.25
        + db_schema_score * 0.15
        + db_seed_score * 0.10
        - hr_penalty * 0.15
        - dup_penalty * 0.05
    )
    quality = max(0, min(100, quality))

    all_entities[ctx_name] = entity_counter.most_common(5)

    summary_rows.append({
        "context": ctx_name,
        "generated": total,
        "errors": data["errors"],
        "schema_aligned": schema_aligned,
        "schema_aligned_pct": f"{schema_score:.1f}%",
        "avg_vocab_score": f"{avg_vocab:.2f}",
        "hr_leakage": hr_leakage_count,
        "db_schema_present": db_schema_present,
        "db_seed_present": db_seed_present,
        "duplicates": duplicate_count,
        "duplicate_pct": f"{duplicate_pct:.1f}%",
        "quality_score": f"{quality:.1f}",
    })

# ──────────────────────────────────────────────────────────────────────────────
# Per-Context Metrics Table
# ──────────────────────────────────────────────────────────────────────────────

print("\n┌─────────────────────────────────────────────────────────────────────┐")
print("│                    PER-CONTEXT METRICS TABLE                        │")
print("└─────────────────────────────────────────────────────────────────────┘")

header = f"{'CONTEXT':<12} {'GEN':>4} {'ERR':>4} {'SCHEMA%':>8} {'AVG_VOC':>8} {'HR_LEAK':>8} {'DB_SCH':>7} {'DB_SEED':>8} {'DUPS':>5} {'DUP%':>6} {'QUALITY':>8}"
print(header)
print("-" * len(header))

for row in summary_rows:
    print(
        f"{row['context']:<12} "
        f"{row['generated']:>4} "
        f"{row['errors']:>4} "
        f"{row['schema_aligned_pct']:>8} "
        f"{row['avg_vocab_score']:>8} "
        f"{row['hr_leakage']:>8} "
        f"{row['db_schema_present']:>7} "
        f"{row['db_seed_present']:>8} "
        f"{row['duplicates']:>5} "
        f"{row['duplicate_pct']:>6} "
        f"{row['quality_score']:>8}"
    )

# ──────────────────────────────────────────────────────────────────────────────
# Top Entities Per Context
# ──────────────────────────────────────────────────────────────────────────────

print("\n┌─────────────────────────────────────────────────────────────────────┐")
print("│                   TOP RECURRING ENTITIES PER CONTEXT               │")
print("└─────────────────────────────────────────────────────────────────────┘")

for ctx_name, entities in all_entities.items():
    if entities:
        ent_str = ", ".join(f"{e}({c})" for e, c in entities)
    else:
        ent_str = "(none detected)"
    print(f"  {ctx_name:<12}: {ent_str}")

# ──────────────────────────────────────────────────────────────────────────────
# Summary
# ──────────────────────────────────────────────────────────────────────────────

print("\n┌─────────────────────────────────────────────────────────────────────┐")
print("│                        OVERALL SUMMARY                             │")
print("└─────────────────────────────────────────────────────────────────────┘")

total_gen = sum(r["generated"] for r in summary_rows)
total_hr = sum(r["hr_leakage"] for r in summary_rows)
total_dups = sum(r["duplicates"] for r in summary_rows)
avg_quality = sum(float(r["quality_score"]) for r in summary_rows) / len(summary_rows)

print(f"  LLM Used          : {'REAL (OpenAI ' + settings.chat_model + ')' if USE_REAL_LLM else 'MOCK (structural audit)'}")
print(f"  Total Generated   : {total_gen}")
print(f"  Total HR Leakage  : {total_hr}")
print(f"  Total Duplicates  : {total_dups}  ({total_dups/total_gen*100:.1f}%)")
print(f"  Avg Quality Score : {avg_quality:.1f} / 100")

print("\n  Per-Context Quality Scores:")
for row in summary_rows:
    score = float(row["quality_score"])
    bar = "█" * int(score / 5) + "░" * (20 - int(score / 5))
    print(f"    {row['context']:<12}: [{bar}] {score:.1f}/100")

print("\n" + "="*70)
print("AUDIT COMPLETE")
print("="*70)

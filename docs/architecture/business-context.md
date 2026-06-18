# BusinessContext Architecture

## Purpose

`BusinessContext` is the canonical domain-classification mechanism for the Question Intelligence subsystem. It encodes the business domain of the company under evaluation, enabling context-aware question generation across coding, SQL, and behavioral tracks.

`BusinessContext` is resolved from the company description provided by the user and propagates through the entire question generation pipeline as an immutable classification.

---

## Core Principles

- **Resolved exactly once** — classification runs at `InterviewContextProfile` construction time.
- **Stored in `InterviewContextProfile`** — single canonical location; no re-derivation.
- **Immutable during an interview** — `business_context` is frozen after resolution.
- **Consumed through registries** — generators never embed domain logic directly; they delegate to `CodingDomainProfileRegistry` and `SchemaRegistry`.
- **`CompanyDescription` preserved as raw input** — the original string is retained unmodified for audit and display purposes.

---

## BusinessContext Enum

| Context      | Purpose                                                                 |
|--------------|-------------------------------------------------------------------------|
| `GENERIC`    | Default fallback. No domain-specific assets. Neutral question framing. |
| `FINTECH`    | Financial services, payments, banking, trading domain.                 |
| `ECOMMERCE`  | Retail, marketplace, cart, inventory, order management domain.         |
| `SAAS`       | Multi-tenant software products, subscription, usage metrics domain.    |
| `HEALTHCARE` | Clinical data, patients, appointments, compliance (HIPAA-adjacent).    |

`GENERIC` is the only context that does not require a registered `CodingDomainProfile` or `SchemaDefinition`.

---

## Resolution Flow

```
Company Description (raw string)
        ↓
BusinessContext.from_company_description()
        ↓
InterviewContextProfile.business_context
        ↓
Question generation pipeline
```

**Threshold behavior**

Classification requires a minimum keyword score before assigning a specific context:

```
business_context_min_keyword_score = 2
```

If no context reaches this threshold, `GENERIC` is assigned.

**Tie-breaking**

When multiple contexts reach the same score, the following priority list determines the winner:

```
FINTECH → ECOMMERCE → SAAS → HEALTHCARE
```

---

## Classification Rules

- **Keyword matching** — each non-generic context owns a keyword set; the company description is scanned for membership.
- **Threshold** — a context is only eligible if its keyword match count meets `business_context_min_keyword_score`.
- **Fallback** — if no context qualifies, `GENERIC` is returned unconditionally.
- **Priority ordering** — ties resolved left-to-right: `FINTECH > ECOMMERCE > SAAS > HEALTHCARE`.
- **`GENERIC` is fallback only** — it has no keyword set and is never selected competitively.

---

## Registry Architecture

```
BusinessContext
        ↓
Registry lookup
        ↓
Context-specific assets
```

### `CodingDomainProfileRegistry`

- Maps each `BusinessContext` to a `CodingDomainProfile`.
- Owns vocabulary hints, scenario anchors, and hidden test hints.
- Raises `KeyError` (or returns `GENERIC` profile) for unregistered contexts.

### `SchemaRegistry`

- Maps each `BusinessContext` to a `SchemaDefinition`.
- Owns table definitions, column semantics, and sample data stubs.
- Used exclusively by the SQL generation pipeline.

Both registries are the SSOT for their respective asset types. No domain-specific string is hardcoded inside generators.

---

## Coding Integration

```
BusinessContext
        ↓
CodingDomainProfileRegistry
        ↓
CodingDomainProfile
        ↓
CodingQuestionGenerator
        ↓
CodingPromptBuilder
```

`CodingDomainProfile` exposes:

- **Vocabulary hints** — domain-relevant nouns injected into the prompt (e.g., `"transaction"`, `"ledger"`).
- **Scenario anchors** — contextual problem framings (e.g., "fraud detection pipeline").
- **Hidden test hints** — edge cases implied by the domain (e.g., negative balances, duplicate orders).

**Supported contexts** — all five enum values have registered profiles. `GENERIC` profile uses neutral vocabulary with no scenario anchors.

---

## SQL Integration

```
BusinessContext
        ↓
SchemaRegistry
        ↓
SchemaDefinition
        ↓
SQLDatabase
        ↓
SQLQuestionGenerator
```

| Context                              | Generation strategy          |
|--------------------------------------|------------------------------|
| `GENERIC`                            | Retrieval + enrichment       |
| `FINTECH`, `ECOMMERCE`, `SAAS`, `HEALTHCARE` | Metadata-only generation |

**Rationale** — specific contexts have deterministic schema structures that allow full question generation from metadata. `GENERIC` lacks a fixed schema, requiring retrieval from a corpus followed by contextual enrichment.

---

## Adding a New BusinessContext

1. Add the enum value to `BusinessContext`.
2. Define and register its keyword set in the classifier.
3. Insert it at the appropriate position in the priority list.
4. Implement and register a `CodingDomainProfile` in `CodingDomainProfileRegistry`.
5. Implement and register a `SchemaDefinition` in `SchemaRegistry`.
6. Register all assets (profile, schema, keywords) in their respective registries.
7. Write unit tests: classification, registry lookup, end-to-end generation.
8. Update this document and `question-intelligence.md`.

---

## Current Extension Capacity

The enum-based approach is appropriate for up to approximately **8 contexts**.

Beyond that threshold, evaluate a taxonomy-based registry with hierarchical matching to avoid classification brittleness and registry bloat.

---

## Architectural Invariants

- `BusinessContext` is **never derived twice** within a single interview session.
- Registries are **SSOT** — domain assets live only in registries, not in generators or prompt builders.
- `GENERIC` **must always exist** — it is the unconditional fallback and must remain registered in all registries.
- Unknown or unregistered contexts **must fallback to `GENERIC`** — no generator may raise on an unrecognized context.
- `BusinessContext` **must not be inferred inside generators** — classification is exclusively the responsibility of `BusinessContext.from_company_description()`.
- `InterviewContextProfile.business_context` is **read-only after construction**.

---

## Related Documents

- [`question-intelligence.md`](./question-intelligence.md)
- [`sql-engine.md`](./sql-engine.md)
- [`coding-engine.md`](./coding-engine.md)
- `ADR-006`

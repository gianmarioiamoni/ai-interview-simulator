# /docs/decisions/adr-002-output-contract-refactor.md

# ADR-002 — Semantic Output Contract

# Status

Accepted

---

# Decision

Replace positional UI output mapping with semantic output contract.

---

# Previous Architecture

UIResponse
    ↓
positional output list

Problems:
- fragile ordering
- silent mismatches
- hard maintenance

---

# New Architecture

UIResponse
    ↓
semantic dict contract
    ↓
UIOutputAdapter
    ↓
Gradio outputs

---

# Benefits

- centralized output contract
- safer evolution
- mismatch prevention
- better readability
- easier testing

---

# Tradeoffs

Introduced:
- adapter layer
- mapping abstraction

Accepted intentionally.
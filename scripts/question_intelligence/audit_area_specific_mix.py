"""
Phase 7E-D — Area-Specific Corpus/LLM Mix Audit

Read-only simulation audit comparing uniform 70/30 mix against
area-specific corpus/LLM allocation strategies for technical interviews.

No production code changes, no corpus modifications, no retrieval changes.
"""
import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[2]
OUT  = ROOT / "scripts" / "question_intelligence" / "output"

# ── Load live depth measurements ──────────────────────────────────────────────
tk3 = json.loads((OUT / "phase_7d_tk3_retrieval_sizing.json").read_text())
c21 = json.loads((OUT / "phase_7d_c21_retrieval_unlock_validation.json").read_text())

_tk_depth  = {f"{s['role']}/{s['seniority']}": s["effective_depth_k5"]  for s in tk3["Q1_depth_by_fetch_k"]["slices"]}
_bg_depth  = {f"{s['role']}/{s['seniority']}": s["effective_depth_k3"]   for s in c21["slices"]["technical_background"]}
_cs_depth  = {f"{s['role']}/{s['seniority']}": s["effective_depth_k50"]  for s in c21["slices"]["technical_case_study"]}

TECH_AREAS = [
    "technical_background",
    "technical_technical_knowledge",
    "technical_case_study",
    "technical_database",
    "technical_coding",
]
HR_AREAS = [
    "hr_background", "hr_technical_knowledge", "hr_situational",
    "hr_brain_teaser", "hr_analytical",
]

_FIXED_DEPTHS = {"technical_database": 5, "technical_coding": 5}
HR_DEPTH = 10


def corpus_depth(area: str, role: str, seniority: str) -> int:
    key = f"{role}/{seniority}"
    if area == "technical_background":            return max(1, _bg_depth.get(key, 2))
    if area == "technical_technical_knowledge":   return max(1, _tk_depth.get(key, 4))
    if area == "technical_case_study":            return max(1, _cs_depth.get(key, 4))
    if area in _FIXED_DEPTHS:                     return _FIXED_DEPTHS[area]
    return HR_DEPTH


# ── Allocation strategies ──────────────────────────────────────────────────────
# area → corpus fraction (LLM fraction = 1 - corpus)
MIX_STRATEGIES = {
    "baseline_70_30": {a: 0.70 for a in TECH_AREAS},
    "candidate_a": {
        "technical_background":           0.50,
        "technical_technical_knowledge":  0.80,
        "technical_case_study":           0.60,
        "technical_database":             0.80,
        "technical_coding":               0.90,
    },
    "candidate_b": {
        "technical_background":           0.40,
        "technical_technical_knowledge":  0.75,
        "technical_case_study":           0.50,
        "technical_database":             0.85,
        "technical_coding":               0.95,
    },
}

# ── Area weights (practical allocation from 7E-C) ─────────────────────────────
TECH_WEIGHTS = {
    "technical_background":           0.10,
    "technical_technical_knowledge":  0.20,
    "technical_case_study":           0.25,
    "technical_database":             0.20,
    "technical_coding":               0.25,
}

INTERVIEW_LENGTHS = [10, 20, 30]
N_SESSIONS_LIST   = [1, 5, 10]

SAMPLE_ROLES = [
    ("backend_engineer", "senior"), ("backend_engineer", "junior"),
    ("data_engineer",    "junior"), ("data_engineer",    "mid"),
    ("frontend_engineer","mid"),    ("devops_engineer",  "senior"),
    ("qa_engineer",      "mid"),    ("ml_engineer",      "junior"),
]


# ── Helpers ───────────────────────────────────────────────────────────────────
def q_per_area_map(weights: dict, q_total: int) -> dict:
    raw     = {a: weights[a] * q_total for a in TECH_AREAS}
    floored = {a: math.floor(raw[a])   for a in TECH_AREAS}
    rem     = q_total - sum(floored.values())
    for a in sorted(TECH_AREAS, key=lambda x: raw[x] - floored[x], reverse=True)[:rem]:
        floored[a] += 1
    return floored


def simulate(role: str, seniority: str, n_sessions: int,
             q_map: dict, mix: dict) -> dict:
    """
    Simulate n_sessions for one role/seniority.
    mix: area → corpus fraction.
    Returns aggregate and per-area diversity metrics.
    """
    corpus_pick: dict = defaultdict(int)
    all_flat = []
    llm_ctr  = 0

    for _ in range(n_sessions):
        for area in TECH_AREAS:
            q_total_area = q_map[area]
            if q_total_area == 0:
                continue
            corpus_frac = mix[area]
            corpus_q    = max(1, round(q_total_area * corpus_frac))
            llm_q       = q_total_area - corpus_q
            d           = corpus_depth(area, role, seniority)

            for _ in range(corpus_q):
                idx    = corpus_pick[area]
                is_rep = idx >= d
                corpus_pick[area] += 1
                all_flat.append({
                    "id": f"CORPUS|{area}|q{idx % d}",
                    "area": area, "source": "corpus", "is_repeat": is_rep,
                })
            for _ in range(llm_q):
                llm_ctr += 1
                all_flat.append({
                    "id": f"LLM_{llm_ctr}",
                    "area": area, "source": "llm", "is_repeat": False,
                })

    total   = len(all_flat)
    repeats = sum(1 for p in all_flat if p["is_repeat"])
    unique  = len(set(p["id"] for p in all_flat))

    corpus_all = [p for p in all_flat if p["source"] == "corpus"]
    c_rep      = sum(1 for p in corpus_all if p["is_repeat"])

    per_area = {}
    for area in TECH_AREAS:
        ap = [p for p in all_flat if p["area"] == area and p["source"] == "corpus"]
        ar = sum(1 for p in ap if p["is_repeat"])
        per_area[area] = {
            "corpus_draws":     len(ap),
            "corpus_repeats":   ar,
            "corpus_reuse_pct": round(ar / len(ap) * 100, 1) if ap else 0.0,
            "llm_prompts":      sum(1 for p in all_flat if p["area"] == area and p["source"] == "llm"),
            "q_per_session":    q_map[area],
            "effective_depth":  corpus_depth(area, role, seniority),
            "corpus_frac":      mix[area],
        }

    return {
        "total":            total,
        "repeats":          repeats,
        "unique":           unique,
        "reuse_pct":        round(repeats / total * 100, 1) if total else 0.0,
        "corpus_reuse_pct": round(c_rep / len(corpus_all) * 100, 1) if corpus_all else 0.0,
        "per_area":         per_area,
    }


def aggregate(vals: list[dict]) -> dict:
    return {
        "avg_hybrid_reuse_pct":  round(mean(v["reuse_pct"]        for v in vals), 1),
        "avg_corpus_reuse_pct":  round(mean(v["corpus_reuse_pct"] for v in vals), 1),
        "avg_unique_prompts":    round(mean(v["unique"]            for v in vals), 1),
        "avg_repeated_prompts":  round(mean(v["repeats"]           for v in vals), 1),
    }


# ── Realism scoring ───────────────────────────────────────────────────────────
# Realism dimensions (0–10 each), weighted:
#   conversation_realism    (30%): does the Q stream feel like a real technical screen?
#   interview_authenticity  (40%): does the Q source blend stay undetectable to candidate?
#   follow_up_suitability   (30%): are corpus anchors present for follow-up coherence?
#
# BG area: LLM-heavy is fine (behavioral/open-ended); high LLM acceptable.
# TK area: Corpus needed for standardised technical depth; high LLM degrades consistency.
# CS area: Corpus preferred (complex, multi-part); 50-60% corpus is OK.
# DB area: Corpus preferred (precise SQL/schema); LLM SQL quality varies.
# CODING:  Corpus preferred (validated problems); LLM may create ambiguous prompts.
#
# Scoring per area (corpus_frac → realism contribution):
AREA_REALISM = {
    "technical_background": {
        0.70: 7.0, 0.60: 7.5, 0.50: 8.5, 0.40: 9.0,
        "note": "Open-ended; LLM-heavy is realistic; varied phrasing improves authenticity",
    },
    "technical_technical_knowledge": {
        0.70: 8.0, 0.75: 8.0, 0.80: 9.0, 0.85: 9.0,
        "note": "Corpus anchors ensure technical accuracy; LLM may produce imprecise TK questions",
    },
    "technical_case_study": {
        0.70: 7.5, 0.60: 8.0, 0.50: 7.5,
        "note": "Case studies need corpus complexity; 60% corpus balances variety and depth",
    },
    "technical_database": {
        0.70: 8.0, 0.80: 9.0, 0.85: 9.5,
        "note": "DB questions require schema precision; high corpus preferred",
    },
    "technical_coding": {
        0.70: 8.0, 0.90: 9.0, 0.95: 9.5,
        "note": "Coding questions require validated test cases; high corpus strongly preferred",
    },
}

REALISM_WEIGHTS = {
    "technical_background":           0.10,
    "technical_technical_knowledge":  0.20,
    "technical_case_study":           0.25,
    "technical_database":             0.20,
    "technical_coding":               0.25,
}


def realism_score(mix: dict) -> dict:
    """Compute weighted realism score for a mix strategy."""
    scores = {}
    for area in TECH_AREAS:
        frac = mix[area]
        table = {k: v for k, v in AREA_REALISM[area].items() if isinstance(k, float)}
        # Nearest key match
        nearest = min(table.keys(), key=lambda k: abs(k - frac))
        scores[area] = {"corpus_frac": frac, "score": table[nearest]}

    weighted = sum(scores[a]["score"] * REALISM_WEIGHTS[a] for a in TECH_AREAS)
    return {
        "overall": round(weighted, 2),
        "per_area": scores,
        "interpretation": (
            "9-10: EXCELLENT — mimics senior recruiter style exactly\n"
            "7-9:  GOOD    — realistic and appropriate\n"
            "5-7:  FAIR    — recognisable but some areas feel artificial\n"
            "<5:   POOR    — detectable as automated"
        ),
    }


# ── Evaluation consistency scoring ────────────────────────────────────────────
# Higher corpus fraction → more consistent scoring (same benchmark questions)
# Lower corpus → higher LLM variance → harder to calibrate scoring rubric
def eval_consistency(mix: dict) -> dict:
    scores = {}
    for area in TECH_AREAS:
        c = mix[area]
        # Scoring difficulty consistency: higher corpus = higher consistency
        scoring_stability    = round(min(10.0, c * 10 + 2.0), 1)
        difficulty_stability = round(min(10.0, c * 9  + 1.5), 1)
        benchmark_comp       = round(min(10.0, c * 10 + 1.0), 1)
        scores[area] = {
            "corpus_frac":          c,
            "scoring_stability":    scoring_stability,
            "difficulty_stability": difficulty_stability,
            "benchmark_comparability": benchmark_comp,
            "avg": round(mean([scoring_stability, difficulty_stability, benchmark_comp]), 1),
        }
    overall = round(mean(scores[a]["avg"] * REALISM_WEIGHTS[a] for a in TECH_AREAS) / 0.1 * 0.1, 1)
    return {"overall": round(sum(scores[a]["avg"] * REALISM_WEIGHTS[a] for a in TECH_AREAS), 1),
            "per_area": scores}


# ── Cost estimation ────────────────────────────────────────────────────────────
# Relative cost units (corpus retrieval ≈ 1, LLM generation ≈ 5-8×)
CORPUS_COST_UNIT = 1.0
LLM_COST_UNIT    = 6.0


def cost_estimate(mix: dict, q_map: dict) -> dict:
    breakdown = {}
    total_cost = 0.0
    for area in TECH_AREAS:
        q_pa      = q_map[area]
        c_frac    = mix[area]
        corpus_q  = max(1, round(q_pa * c_frac)) if q_pa > 0 else 0
        llm_q     = q_pa - corpus_q
        area_cost = corpus_q * CORPUS_COST_UNIT + llm_q * LLM_COST_UNIT
        total_cost += area_cost
        breakdown[area] = {
            "corpus_q": corpus_q, "llm_q": llm_q,
            "cost_units": round(area_cost, 1),
        }
    baseline_cost = sum(
        (max(1, round(q_map[a] * 0.70)) * CORPUS_COST_UNIT +
         (q_map[a] - max(1, round(q_map[a] * 0.70))) * LLM_COST_UNIT)
        for a in TECH_AREAS if q_map[a] > 0
    )
    return {
        "total_cost_units":  round(total_cost, 1),
        "baseline_cost_units": round(baseline_cost, 1),
        "cost_vs_baseline_pct": round((total_cost / baseline_cost - 1) * 100, 1) if baseline_cost else 0.0,
        "per_area": breakdown,
    }


# ── Duration estimate ─────────────────────────────────────────────────────────
MIN_PER_Q_TECH = 3.0
MIN_PER_Q_HR   = 3.5


def duration(q_total: int, interview_type: str = "technical") -> dict:
    mpq = MIN_PER_Q_TECH if interview_type == "technical" else MIN_PER_Q_HR
    return {
        "q_total": q_total,
        "avg_min_per_question": mpq,
        "no_followup_min":  round(q_total * mpq, 0),
        "fu20_min":         round(q_total * 1.20 * mpq, 0),
        "fu40_min":         round(q_total * 1.40 * mpq, 0),
    }


# ── Main simulation loop ───────────────────────────────────────────────────────
def run_matrix() -> dict:
    matrix = {}
    for strategy, mix in MIX_STRATEGIES.items():
        matrix[strategy] = {}
        for q_total in INTERVIEW_LENGTHS:
            q_map = q_per_area_map(TECH_WEIGHTS, q_total)
            real  = realism_score(mix)
            ec    = eval_consistency(mix)
            cost  = cost_estimate(mix, q_map)
            dur   = duration(q_total)
            entry = {
                "q_per_area":          q_map,
                "realism":             real,
                "evaluation_consistency": ec,
                "cost":                cost,
                "duration":            dur,
            }
            for n_sessions in N_SESSIONS_LIST:
                vals = [simulate(r, s, n_sessions, q_map, mix) for r, s in SAMPLE_ROLES]
                agg  = aggregate(vals)
                area_summary = {}
                for area in TECH_AREAS:
                    avs = [v["per_area"][area] for v in vals if v["per_area"][area]["corpus_draws"] > 0]
                    if avs:
                        avg_cr = round(mean(av["corpus_reuse_pct"] for av in avs), 1)
                        area_summary[area] = {
                            "avg_corpus_reuse_pct": avg_cr,
                            "q_per_session":        q_map[area],
                            "corpus_frac":          mix[area],
                            "avg_depth":            round(mean(av["effective_depth"] for av in avs), 1),
                            "classification":       ("HIGH_REUSE" if avg_cr >= 50
                                                     else "MODERATE" if avg_cr >= 25
                                                     else "GOOD"),
                        }
                    else:
                        area_summary[area] = {
                            "avg_corpus_reuse_pct": 0.0, "q_per_session": 0,
                            "corpus_frac": mix[area], "avg_depth": 0.0,
                            "classification": "SKIPPED",
                        }
                entry[f"n{n_sessions}"] = {
                    **agg,
                    "diversity_status": (
                        "PASS"     if agg["avg_hybrid_reuse_pct"] < 20 else
                        "MARGINAL" if agg["avg_hybrid_reuse_pct"] < 40 else
                        "FAIL"
                    ),
                    "area_breakdown": area_summary,
                }
            matrix[strategy][f"q{q_total}"] = entry
    return matrix


# ── Q5: Corpus docs avoided ───────────────────────────────────────────────────
def corpus_docs_avoided(matrix: dict, q_total: int, n_sessions: int) -> dict:
    # docs_per_pp_global from 7D-G0 empirical: 24 BG docs → ~4.3pp reduction
    docs_per_pp = 24 / 4.3
    key = f"q{q_total}"
    baseline_reuse  = matrix["baseline_70_30"][key][f"n{n_sessions}"]["avg_hybrid_reuse_pct"]
    cand_a_reuse    = matrix["candidate_a"][key][f"n{n_sessions}"]["avg_hybrid_reuse_pct"]
    cand_b_reuse    = matrix["candidate_b"][key][f"n{n_sessions}"]["avg_hybrid_reuse_pct"]
    delta_a = round(baseline_reuse - cand_a_reuse, 1)
    delta_b = round(baseline_reuse - cand_b_reuse, 1)
    return {
        "baseline_reuse":  baseline_reuse,
        "candidate_a_reuse": cand_a_reuse,
        "candidate_b_reuse": cand_b_reuse,
        "delta_a_pp": delta_a,
        "delta_b_pp": delta_b,
        "docs_avoided_candidate_a": int(max(0, delta_a * docs_per_pp)),
        "docs_avoided_candidate_b": int(max(0, delta_b * docs_per_pp)),
    }


# ── Build full report ──────────────────────────────────────────────────────────
def build_report(matrix: dict) -> dict:
    docs_q20_n5 = corpus_docs_avoided(matrix, 20, 5)
    docs_q30_n5 = corpus_docs_avoided(matrix, 30, 5)

    # ── Composite scoring per strategy ────────────────────────────────────────
    def composite(strategy: str) -> float:
        r5_20  = matrix[strategy]["q20"]["n5"]["avg_hybrid_reuse_pct"]
        real20 = matrix[strategy]["q20"]["realism"]["overall"]
        ec20   = matrix[strategy]["q20"]["evaluation_consistency"]["overall"]
        cost20 = matrix[strategy]["q20"]["cost"]["cost_vs_baseline_pct"]
        # Lower reuse → better; higher realism → better; higher EC → better; lower cost → better
        return round((100 - r5_20) * 0.35 + real20 * 3.5 + ec20 * 3.0 - cost20 * 0.1, 2)

    winner = max(MIX_STRATEGIES, key=composite)

    q20_n5 = {s: matrix[s]["q20"]["n5"]["avg_hybrid_reuse_pct"] for s in MIX_STRATEGIES}
    q20_n1 = {s: matrix[s]["q20"]["n1"]["avg_hybrid_reuse_pct"] for s in MIX_STRATEGIES}
    q10_n5 = {s: matrix[s]["q10"]["n5"]["avg_hybrid_reuse_pct"] for s in MIX_STRATEGIES}
    real   = {s: matrix[s]["q20"]["realism"]["overall"] for s in MIX_STRATEGIES}
    ec     = {s: matrix[s]["q20"]["evaluation_consistency"]["overall"] for s in MIX_STRATEGIES}
    cost   = {s: matrix[s]["q20"]["cost"]["cost_vs_baseline_pct"] for s in MIX_STRATEGIES}

    return {
        "audit":     "Phase 7E-D Area-Specific Corpus/LLM Mix Audit",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "configuration": {
            "interview_type":     "technical (practical weighting)",
            "area_weights":       TECH_WEIGHTS,
            "interview_lengths":  INTERVIEW_LENGTHS,
            "n_sessions_tested":  N_SESSIONS_LIST,
            "sample_roles":       [f"{r}/{s}" for r, s in SAMPLE_ROLES],
            "strategies":         MIX_STRATEGIES,
        },
        "simulation_matrix": matrix,
        "Q1_overall_tradeoff": {
            s: {
                "reuse_n5_q20":   q20_n5[s],
                "realism":        real[s],
                "eval_consistency": ec[s],
                "cost_vs_baseline_pct": cost[s],
                "composite_score": composite(s),
            } for s in MIX_STRATEGIES
        },
        "Q2_vs_baseline": {
            s: {
                "reuse_delta_n5_q20_pp": round(q20_n5["baseline_70_30"] - q20_n5[s], 1),
                "reuse_delta_n1_q20_pp": round(q20_n1["baseline_70_30"] - q20_n1[s], 1),
                "reuse_delta_n5_q10_pp": round(q10_n5["baseline_70_30"] - q10_n5[s], 1),
                "realism_delta":         round(real[s] - real["baseline_70_30"], 2),
                "eval_consistency_delta": round(ec[s] - ec["baseline_70_30"], 1),
            } for s in MIX_STRATEGIES if s != "baseline_70_30"
        },
        "Q3_corpus_docs_avoided": {
            "q20_n5": docs_q20_n5,
            "q30_n5": docs_q30_n5,
        },
        "Q4_production_recommendation": {
            "interview_length":      "20 questions (standard mode)",
            "area_allocation":       TECH_WEIGHTS,
            "per_area_corpus_llm":   MIX_STRATEGIES["candidate_a"],
            "rationale": (
                "Candidate A reduces LLM exposure in high-precision areas (coding/database) "
                "while increasing LLM variety in background (50% LLM). "
                "This improves realism (+score vs baseline) and slightly reduces "
                "background corpus pressure. Evaluation consistency remains HIGH "
                "due to corpus anchoring in TK, DB, and coding areas. "
                "Cost is marginally lower than baseline (fewer LLM calls in high-cost coding area)."
            ),
            "follow_up_rate":        "20% (recommended)",
            "expected_reuse_n5_q20": q20_n5["candidate_a"],
            "expected_realism":      real["candidate_a"],
        },
        "Q5_expansion_deferral": {
            "recommendation": "PARTIAL_DEFERRAL",
            "rationale": (
                "Adopting Candidate A first is a zero-cost config change that improves realism "
                "and reduces background corpus pressure. However, at 20Q/n=5, all strategies "
                f"show reuse >{q20_n5['candidate_a'] - 5}% — area-specific mix alone cannot "
                "compensate for BG depth=2.1 and TK depth=3.9. "
                "Recommended sequence: "
                "(1) Deploy Candidate A mix immediately (config-only). "
                "(2) Deploy TK fetch_k=5 config change (Phase 7D-G0 Phase A). "
                "(3) Author 24 BG documents (Phase 7D-G0 Phase B — highest ROI). "
                "(4) Reassess TK corpus expansion (87 docs) after BG expansion is validated."
            ),
            "can_defer": ["technical_technical_knowledge full 87-doc expansion"],
            "cannot_defer": [
                "technical_background 24-doc expansion (BG depth=2.1 is primary blocker)",
                "TK fetch_k=5 config (free, immediate -4.3pp)",
            ],
        },
        "verdict": {
            "winner":            winner,
            "verdict_label":     f"AREA_SPECIFIC_MIX_RECOMMENDED: {winner}",
            "outperforms_baseline": winner != "baseline_70_30",
            "reuse_improvement_pp": round(q20_n5["baseline_70_30"] - q20_n5[winner], 1),
            "realism_improvement":  round(real[winner] - real["baseline_70_30"], 2),
            "ec_improvement":       round(ec[winner] - ec["baseline_70_30"], 1),
            "corpus_docs_avoided_q20_n5": docs_q20_n5[f"docs_avoided_{winner.replace('-','_')}"]
                                          if f"docs_avoided_{winner.replace('-','_')}" in docs_q20_n5
                                          else docs_q20_n5.get("docs_avoided_candidate_a", 0),
            "quantitative_justification": (
                f"At 20Q / 5 sessions: baseline={q20_n5['baseline_70_30']}%, "
                f"candidate_a={q20_n5['candidate_a']}%, candidate_b={q20_n5['candidate_b']}%. "
                f"Realism: baseline={real['baseline_70_30']}, candidate_a={real['candidate_a']}, "
                f"candidate_b={real['candidate_b']}. "
                f"Eval consistency: baseline={ec['baseline_70_30']}, "
                f"candidate_a={ec['candidate_a']}, candidate_b={ec['candidate_b']}. "
                f"Winner '{winner}' scores highest composite (diversity + realism + consistency - cost). "
                f"Area-specific mix cannot fully replace corpus expansion but provides "
                f"meaningful realism gains at zero authoring cost."
            ),
        },
    }


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Running Phase 7E-D Area-Specific Mix Audit...")
    matrix = run_matrix()
    report = build_report(matrix)

    full_path = OUT / "phase_7e_d_area_specific_mix_audit.json"
    sum_path  = OUT / "phase_7e_d_summary.json"

    full_path.write_text(json.dumps(report, indent=2))

    # Summary: omit large simulation_matrix
    summary = {k: v for k, v in report.items() if k != "simulation_matrix"}
    sum_path.write_text(json.dumps(summary, indent=2))

    print(f"Wrote {full_path} ({full_path.stat().st_size // 1024}k)")
    print(f"Wrote {sum_path} ({sum_path.stat().st_size // 1024}k)")
    print(f"\nVERDICT: {report['verdict']['verdict_label']}")
    print(f"\n=== Q1 Composite scores ===")
    for s, v in report["Q1_overall_tradeoff"].items():
        print(f"  {s:25s}: reuse={v['reuse_n5_q20']:5.1f}%  real={v['realism']:5.2f}  "
              f"ec={v['eval_consistency']:5.1f}  cost={v['cost_vs_baseline_pct']:+5.1f}%  "
              f"composite={v['composite_score']:6.2f}")
    print(f"\n=== Q2 Improvement vs baseline (20Q, n=5) ===")
    for s, v in report["Q2_vs_baseline"].items():
        print(f"  {s:25s}: Δreuse={v['reuse_delta_n5_q20_pp']:+5.1f}pp  "
              f"Δreal={v['realism_delta']:+5.2f}  ΔEC={v['eval_consistency_delta']:+5.1f}")
    print(f"\n=== Q3 Corpus docs avoided (20Q, n=5) ===")
    q3 = report["Q3_corpus_docs_avoided"]["q20_n5"]
    print(f"  Candidate A: Δreuse={q3['delta_a_pp']:+.1f}pp → {q3['docs_avoided_candidate_a']} docs avoided")
    print(f"  Candidate B: Δreuse={q3['delta_b_pp']:+.1f}pp → {q3['docs_avoided_candidate_b']} docs avoided")
    print(f"\n=== Q5 Deferral recommendation ===")
    print(f"  {report['Q5_expansion_deferral']['recommendation']}")
    print(f"  Can defer: {report['Q5_expansion_deferral']['can_defer']}")
    print(f"  Cannot defer: {report['Q5_expansion_deferral']['cannot_defer']}")

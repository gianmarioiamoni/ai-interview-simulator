# app/ui/mappers/gating_reason_mapper.py

# Maps internal gating reasons to user-friendly messages

def map_gating_reason(reason: str | None) -> str | None:

    if not reason:
        return None

    mapping = {
        "system_design_below_threshold": "System Design performance is below the expected threshold for this role. This impacts the final hiring decision.",
        "technical_depth_below_threshold": "Technical depth is below the required level, limiting confidence in core engineering capabilities.",
        "problem_solving_below_threshold": "Problem solving performance is below expectations, indicating difficulties in handling complex scenarios.",
    }

    return mapping.get(
        reason, "One or more critical areas did not meet the required threshold."
    )

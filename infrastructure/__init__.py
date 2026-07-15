# infrastructure/__init__.py
# EPIC-02 — P4/C1 — Repository dependency injection wiring
#
# Exposes the concrete LongitudinalProfileRepository implementation for
# dependency injection into LongitudinalUpdateNode.
# Governing: ADR-034 Decision 8, EPIC-02-IMPLEMENTATION-PLAN.md P4-C1.
#
# Import is deferred to avoid circular import chains that arise when
# infrastructure.config.settings is resolved during module initialisation.
# Callers should import JsonFileLongitudinalProfileRepository directly from
# infrastructure.longitudinal.longitudinal_profile_repository_impl.


def get_longitudinal_profile_repository_class():
    """Return JsonFileLongitudinalProfileRepository for dependency injection.

    Lazy import avoids circular initialisation between infrastructure.config.settings
    and the domain contracts imported by the repository implementation.
    """
    from infrastructure.longitudinal.longitudinal_profile_repository_impl import (
        JsonFileLongitudinalProfileRepository,
    )
    return JsonFileLongitudinalProfileRepository

# tests/domain/contracts/longitudinal/test_longitudinal_profile_repository.py
# P1/C3 unit tests — LongitudinalProfileRepository interface and package exports.

from __future__ import annotations

import inspect
from abc import ABC
from typing import Optional

import pytest

from domain.contracts.longitudinal import (
    CrossSessionLanguageCapability,
    LongitudinalProfile,
    LongitudinalProfileBuilder,
    LongitudinalProfileRepository,
    LongitudinalSessionEntry,
    LongitudinalSessionMetadata,
)
from domain.contracts.longitudinal.longitudinal_profile_repository import (
    LongitudinalProfileRepository as _RepoDirectImport,
)


# ===========================================================================
# Repository interface is abstract
# ===========================================================================


class TestRepositoryIsAbstract:

    def test_repository_is_abstract_class(self) -> None:
        assert issubclass(LongitudinalProfileRepository, ABC)

    def test_repository_cannot_be_instantiated_directly(self) -> None:
        with pytest.raises(TypeError):
            LongitudinalProfileRepository()  # type: ignore[abstract]

    def test_get_is_abstract(self) -> None:
        assert getattr(LongitudinalProfileRepository.get, "__isabstractmethod__", False)

    def test_save_is_abstract(self) -> None:
        assert getattr(LongitudinalProfileRepository.save, "__isabstractmethod__", False)

    def test_exists_is_abstract(self) -> None:
        assert getattr(LongitudinalProfileRepository.exists, "__isabstractmethod__", False)

    def test_exactly_three_abstract_methods(self) -> None:
        abstract_methods = {
            name
            for name, method in inspect.getmembers(LongitudinalProfileRepository, predicate=inspect.isfunction)
            if getattr(method, "__isabstractmethod__", False)
        }
        assert abstract_methods == {"get", "save", "exists"}

    def test_concrete_subclass_without_all_methods_not_instantiable(self) -> None:
        class Incomplete(LongitudinalProfileRepository):
            def get(self, candidate_identity_id: str) -> Optional[LongitudinalProfile]:
                return None
            # Missing save and exists

        with pytest.raises(TypeError):
            Incomplete()  # type: ignore[abstract]

    def test_concrete_subclass_with_all_methods_instantiable(self) -> None:
        class Complete(LongitudinalProfileRepository):
            def get(self, candidate_identity_id: str) -> Optional[LongitudinalProfile]:
                return None

            def save(self, profile: LongitudinalProfile) -> None:
                pass

            def exists(self, candidate_identity_id: str) -> bool:
                return False

        repo = Complete()
        assert repo.get("cand-001") is None
        assert repo.exists("cand-001") is False

    def test_method_signatures_match_spec(self) -> None:
        sig_get = inspect.signature(LongitudinalProfileRepository.get)
        sig_save = inspect.signature(LongitudinalProfileRepository.save)
        sig_exists = inspect.signature(LongitudinalProfileRepository.exists)

        assert "candidate_identity_id" in sig_get.parameters
        assert "profile" in sig_save.parameters
        assert "candidate_identity_id" in sig_exists.parameters


# ===========================================================================
# Package exports (__init__.py)
# ===========================================================================


class TestPackageExports:

    def test_longitudinal_profile_exported(self) -> None:
        assert LongitudinalProfile is not None

    def test_longitudinal_session_entry_exported(self) -> None:
        assert LongitudinalSessionEntry is not None

    def test_longitudinal_session_metadata_exported(self) -> None:
        assert LongitudinalSessionMetadata is not None

    def test_cross_session_language_capability_exported(self) -> None:
        assert CrossSessionLanguageCapability is not None

    def test_longitudinal_profile_builder_exported(self) -> None:
        assert LongitudinalProfileBuilder is not None

    def test_longitudinal_profile_repository_exported(self) -> None:
        assert LongitudinalProfileRepository is not None

    def test_direct_import_equals_package_import(self) -> None:
        assert LongitudinalProfileRepository is _RepoDirectImport

    def test_all_exports_accessible_from_package(self) -> None:
        import domain.contracts.longitudinal as pkg
        for name in pkg.__all__:
            assert hasattr(pkg, name), f"__all__ member {name!r} not accessible from package"

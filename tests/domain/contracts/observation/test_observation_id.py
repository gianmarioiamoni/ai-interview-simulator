# tests/domain/contracts/observation/test_observation_id.py

import uuid

import pytest
from pydantic import ValidationError

from domain.contracts.observation.observation_id import ObservationId


class TestObservationIdConstruction:
    def test_default_generates_valid_uuid(self):
        oid = ObservationId()
        uuid.UUID(oid.value, version=4)  # raises if invalid

    def test_generate_classmethod_returns_instance(self):
        oid = ObservationId.generate()
        assert isinstance(oid, ObservationId)

    def test_generate_produces_unique_ids(self):
        ids = {ObservationId.generate().value for _ in range(100)}
        assert len(ids) == 100

    def test_explicit_valid_uuid(self):
        v = str(uuid.uuid4())
        oid = ObservationId(value=v)
        assert oid.value == v

    def test_schema_version_default(self):
        oid = ObservationId()
        assert oid.schema_version == "1.0"

    def test_explicit_schema_version(self):
        oid = ObservationId(value=str(uuid.uuid4()), schema_version="2.0")
        assert oid.schema_version == "2.0"


class TestObservationIdImmutability:
    def test_frozen(self):
        oid = ObservationId()
        with pytest.raises(ValidationError):
            oid.value = str(uuid.uuid4())

    def test_extra_fields_forbidden(self):
        with pytest.raises(ValidationError):
            ObservationId(value=str(uuid.uuid4()), extra_field="x")  # type: ignore[call-arg]


class TestObservationIdValidation:
    def test_invalid_uuid_raises(self):
        with pytest.raises(ValidationError):
            ObservationId(value="not-a-uuid")

    def test_empty_string_raises(self):
        with pytest.raises(ValidationError):
            ObservationId(value="")

    def test_short_string_raises(self):
        with pytest.raises(ValidationError):
            ObservationId(value="short")

    def test_non_uuid_string_rejected(self):
        with pytest.raises(ValidationError):
            ObservationId(value="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx")


class TestObservationIdEquality:
    def test_same_value_equal(self):
        v = str(uuid.uuid4())
        a = ObservationId(value=v)
        b = ObservationId(value=v)
        assert a == b

    def test_different_values_not_equal(self):
        a = ObservationId.generate()
        b = ObservationId.generate()
        assert a != b

    def test_hash_consistency(self):
        v = str(uuid.uuid4())
        a = ObservationId(value=v)
        b = ObservationId(value=v)
        assert hash(a) == hash(b)

    def test_usable_as_dict_key(self):
        oid = ObservationId.generate()
        d = {oid: "value"}
        assert d[oid] == "value"

    def test_str_returns_value(self):
        v = str(uuid.uuid4())
        oid = ObservationId(value=v)
        assert str(oid) == v

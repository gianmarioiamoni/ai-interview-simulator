# tests/domain/contracts/observation/test_observation_query.py

import pytest
from pydantic import ValidationError

from domain.contracts.observation.observation_filter import ObservationFilter
from domain.contracts.observation.observation_query import (
    ObservationQuery,
    ObservationSortField,
    ObservationSortOrder,
)


class TestObservationQueryDefaults:
    def test_filter_defaults_to_empty(self):
        q = ObservationQuery()
        assert isinstance(q.filter, ObservationFilter)

    def test_sort_by_default(self):
        q = ObservationQuery()
        assert q.sort_by == ObservationSortField.QUESTION_INDEX

    def test_sort_order_default(self):
        q = ObservationQuery()
        assert q.sort_order == ObservationSortOrder.ASC

    def test_limit_default(self):
        q = ObservationQuery()
        assert q.limit == 100

    def test_offset_default(self):
        q = ObservationQuery()
        assert q.offset == 0

    def test_schema_version_default(self):
        q = ObservationQuery()
        assert q.schema_version == "1.0"


class TestObservationQueryImmutability:
    def test_frozen(self):
        q = ObservationQuery()
        with pytest.raises(ValidationError):
            q.limit = 50

    def test_extra_fields_forbidden(self):
        with pytest.raises(ValidationError):
            ObservationQuery(extra="x")  # type: ignore[call-arg]


class TestObservationQueryValidation:
    def test_limit_min_one(self):
        q = ObservationQuery(limit=1)
        assert q.limit == 1

    def test_limit_zero_raises(self):
        with pytest.raises(ValidationError):
            ObservationQuery(limit=0)

    def test_limit_max_1000(self):
        q = ObservationQuery(limit=1000)
        assert q.limit == 1000

    def test_limit_above_max_raises(self):
        with pytest.raises(ValidationError):
            ObservationQuery(limit=1001)

    def test_offset_zero_valid(self):
        q = ObservationQuery(offset=0)
        assert q.offset == 0

    def test_negative_offset_raises(self):
        with pytest.raises(ValidationError):
            ObservationQuery(offset=-1)

    def test_large_offset_valid(self):
        q = ObservationQuery(offset=10000)
        assert q.offset == 10000


class TestObservationSortField:
    def test_question_index_value(self):
        assert ObservationSortField.QUESTION_INDEX == "question_index"

    def test_observed_at_value(self):
        assert ObservationSortField.OBSERVED_AT == "observed_at"

    def test_confidence_value(self):
        assert ObservationSortField.CONFIDENCE == "confidence"

    def test_weight_value(self):
        assert ObservationSortField.WEIGHT == "weight"

    def test_is_str_enum(self):
        assert isinstance(ObservationSortField.CONFIDENCE, str)


class TestObservationSortOrder:
    def test_asc_value(self):
        assert ObservationSortOrder.ASC == "asc"

    def test_desc_value(self):
        assert ObservationSortOrder.DESC == "desc"

    def test_is_str_enum(self):
        assert isinstance(ObservationSortOrder.ASC, str)


class TestObservationQueryComposition:
    def test_custom_filter_stored(self):
        f = ObservationFilter(session_id="my-sess")
        q = ObservationQuery(filter=f)
        assert q.filter.session_id == "my-sess"

    def test_all_sort_fields_constructable(self):
        for field in ObservationSortField:
            q = ObservationQuery(sort_by=field)
            assert q.sort_by == field

    def test_all_sort_orders_constructable(self):
        for order in ObservationSortOrder:
            q = ObservationQuery(sort_order=order)
            assert q.sort_order == order

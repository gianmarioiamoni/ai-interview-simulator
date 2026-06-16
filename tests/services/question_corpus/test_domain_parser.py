# tests/services/question_corpus/test_domain_parser.py

import pytest

from services.question_corpus.utils.domain_parser import parse_domains, serialize_domains


class TestParseDomains:
    def test_list_input(self):
        assert parse_domains(["join", "aggregation", "group_by"]) == [
            "join",
            "aggregation",
            "group_by",
        ]

    def test_csv_string_input(self):
        assert parse_domains("join,aggregation,group_by") == [
            "join",
            "aggregation",
            "group_by",
        ]

    def test_csv_with_spaces(self):
        assert parse_domains("join, aggregation , group_by") == [
            "join",
            "aggregation",
            "group_by",
        ]

    def test_none_input(self):
        assert parse_domains(None) == []

    def test_empty_string(self):
        assert parse_domains("") == []

    def test_empty_list(self):
        assert parse_domains([]) == []

    def test_list_with_empty_tokens(self):
        assert parse_domains(["join", "", "  ", "aggregation"]) == [
            "join",
            "aggregation",
        ]

    def test_csv_with_trailing_comma(self):
        assert parse_domains("join,aggregation,") == ["join", "aggregation"]

    def test_single_value_list(self):
        assert parse_domains(["technical_database"]) == ["technical_database"]

    def test_single_value_string(self):
        assert parse_domains("technical_database") == ["technical_database"]


class TestSerializeDomains:
    def test_list_to_csv(self):
        assert serialize_domains(["join", "aggregation", "group_by"]) == (
            "join,aggregation,group_by"
        )

    def test_string_unchanged(self):
        assert serialize_domains("join,aggregation") == "join,aggregation"

    def test_none_to_empty_string(self):
        assert serialize_domains(None) == ""

    def test_empty_list_to_empty_string(self):
        assert serialize_domains([]) == ""

    def test_empty_string_unchanged(self):
        assert serialize_domains("") == ""

    def test_list_with_whitespace_stripped(self):
        assert serialize_domains(["join", " aggregation ", "group_by"]) == (
            "join,aggregation,group_by"
        )

    def test_list_with_empty_tokens_ignored(self):
        assert serialize_domains(["join", "", "aggregation"]) == "join,aggregation"

    def test_already_serialized_string_not_double_joined(self):
        already = "join,aggregation,group_by"
        assert serialize_domains(already) == already


class TestRoundTrip:
    def test_list_serialize_then_parse(self):
        original = ["join", "aggregation", "group_by"]
        assert parse_domains(serialize_domains(original)) == original

    def test_csv_parse_then_serialize(self):
        csv = "join,aggregation,group_by"
        assert serialize_domains(parse_domains(csv)) == csv

    def test_none_serialize_then_parse_is_empty(self):
        assert parse_domains(serialize_domains(None)) == []

    def test_empty_list_roundtrip(self):
        assert parse_domains(serialize_domains([])) == []

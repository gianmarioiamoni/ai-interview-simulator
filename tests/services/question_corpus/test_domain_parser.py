# tests/services/question_corpus/test_domain_parser.py

import pytest

from domain.contracts.question.sql_domain import SqlDomain
from services.question_corpus.utils.domain_parser import (
    parse_domains,
    parse_sql_domains,
    serialize_domains,
)


class TestParseSqlDomains:
    def test_list_input(self):
        assert parse_sql_domains(["join", "group_by", "having"]) == [
            SqlDomain.JOIN,
            SqlDomain.GROUP_BY,
            SqlDomain.HAVING,
        ]

    def test_csv_string_input(self):
        assert parse_sql_domains("join,group_by,having") == [
            SqlDomain.JOIN,
            SqlDomain.GROUP_BY,
            SqlDomain.HAVING,
        ]

    def test_csv_with_spaces(self):
        assert parse_sql_domains("join, group_by , having") == [
            SqlDomain.JOIN,
            SqlDomain.GROUP_BY,
            SqlDomain.HAVING,
        ]

    def test_none_input(self):
        assert parse_sql_domains(None) == []

    def test_empty_string(self):
        assert parse_sql_domains("") == []

    def test_empty_list(self):
        assert parse_sql_domains([]) == []

    def test_unknown_value_falls_back_to_technical_database(self):
        result = parse_sql_domains(["join", "unknown_domain"])
        assert result == [SqlDomain.JOIN, SqlDomain.TECHNICAL_DATABASE]

    def test_list_with_empty_tokens(self):
        assert parse_sql_domains(["join", "", "  ", "having"]) == [
            SqlDomain.JOIN,
            SqlDomain.HAVING,
        ]

    def test_csv_with_trailing_comma(self):
        assert parse_sql_domains("join,having,") == [SqlDomain.JOIN, SqlDomain.HAVING]

    def test_single_value_list(self):
        assert parse_sql_domains(["technical_database"]) == [SqlDomain.TECHNICAL_DATABASE]

    def test_single_value_string(self):
        assert parse_sql_domains("technical_database") == [SqlDomain.TECHNICAL_DATABASE]

    def test_all_valid_domains(self):
        values = [d.value for d in SqlDomain]
        result = parse_sql_domains(values)
        assert result == list(SqlDomain)

    def test_sql_domain_enum_passthrough(self):
        assert parse_sql_domains([SqlDomain.JOIN, SqlDomain.CTE]) == [
            SqlDomain.JOIN,
            SqlDomain.CTE,
        ]


class TestParseDomains:
    """Backward-compat wrapper — returns list[str] (enum .values)."""

    def test_list_input(self):
        assert parse_domains(["join", "group_by", "having"]) == [
            "join",
            "group_by",
            "having",
        ]

    def test_csv_string_input(self):
        assert parse_domains("join,group_by,having") == ["join", "group_by", "having"]

    def test_none_input(self):
        assert parse_domains(None) == []

    def test_empty_string(self):
        assert parse_domains("") == []

    def test_unknown_falls_back_to_technical_database_string(self):
        result = parse_domains(["join", "unknown_thing"])
        assert result == ["join", "technical_database"]

    def test_single_value_list(self):
        assert parse_domains(["technical_database"]) == ["technical_database"]


class TestSerializeDomains:
    def test_list_str_to_csv(self):
        assert serialize_domains(["join", "group_by", "having"]) == "join,group_by,having"

    def test_list_sql_domain_to_csv(self):
        assert serialize_domains([SqlDomain.JOIN, SqlDomain.GROUP_BY]) == "join,group_by"

    def test_string_unchanged(self):
        assert serialize_domains("join,group_by") == "join,group_by"

    def test_none_to_empty_string(self):
        assert serialize_domains(None) == ""

    def test_empty_list_to_empty_string(self):
        assert serialize_domains([]) == ""

    def test_empty_string_unchanged(self):
        assert serialize_domains("") == ""

    def test_list_with_whitespace_stripped(self):
        assert serialize_domains(["join", " group_by ", "having"]) == "join,group_by,having"

    def test_list_with_empty_tokens_ignored(self):
        assert serialize_domains(["join", "", "having"]) == "join,having"

    def test_already_serialized_string_not_double_joined(self):
        already = "join,group_by,having"
        assert serialize_domains(already) == already


class TestRoundTrip:
    def test_list_serialize_then_parse(self):
        original = [SqlDomain.JOIN, SqlDomain.GROUP_BY, SqlDomain.HAVING]
        assert parse_sql_domains(serialize_domains(original)) == original

    def test_csv_parse_then_serialize(self):
        csv = "join,group_by,having"
        assert serialize_domains(parse_sql_domains(csv)) == csv

    def test_none_serialize_then_parse_is_empty(self):
        assert parse_sql_domains(serialize_domains(None)) == []

    def test_empty_list_roundtrip(self):
        assert parse_sql_domains(serialize_domains([])) == []

from services.sql_engine.sql_database import SQLDatabase
from services.sql_engine.schema_summary_generator import (
    SchemaSummaryGenerator,
)


def test_schema_summary_contains_tables_and_columns():
    db = SQLDatabase()
    generator = SchemaSummaryGenerator()

    summary = generator.generate(db.connection)

    assert "Table departments:" in summary
    assert "Table employees:" in summary
    assert "Table projects:" in summary
    assert "Table employee_projects:" in summary

    assert "id (INTEGER)" in summary
    assert "name (TEXT)" in summary
    assert "salary (INTEGER)" in summary

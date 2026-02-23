from services.sql_engine.sql_database import SQLDatabase


def test_database_initialization():
    db = SQLDatabase()
    conn = db.connection
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM departments")
    departments_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM employees")
    employees_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM projects")
    projects_count = cursor.fetchone()[0]

    assert departments_count == 3
    assert employees_count == 4
    assert projects_count == 2


def test_simple_query():
    db = SQLDatabase()
    conn = db.connection
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM employees WHERE salary > 80000")
    result = cursor.fetchall()

    assert ("Alice",) in result

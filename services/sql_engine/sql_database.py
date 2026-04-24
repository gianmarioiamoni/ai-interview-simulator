# services/sql_engine/sql_database.py

# SQLDatabase
#
# Responsibility:
# - Creates an in-memory SQLite database
# - Initializes IT company schema
# - Loads deterministic dataset
# - Exposes connection for query execution

import sqlite3


class SQLDatabase:
    def __init__(self) -> None:
        self._schema_sql = self._get_schema_sql_internal()
        self._seed_sql = self._get_seed_sql_internal()
        self._connection = sqlite3.connect(":memory:")
        self._initialize_schema()
        self._load_data()

    @property
    def connection(self) -> sqlite3.Connection:
        return self._connection

    def get_schema_sql(self) -> str:
        return self._schema_sql

    def get_seed_sql(self) -> str:
        return self._seed_sql

    # 👉 opzionale ma consigliato
    def get_fresh_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(":memory:")
        cursor = conn.cursor()

        cursor.executescript(self._schema_sql)
        cursor.executescript(self._seed_sql)
        self._connection.commit()

        return conn

    def _initialize_schema(self) -> None:
        cursor = self._connection.cursor()

        cursor.executescript(
            """
        CREATE TABLE departments (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL
        );

        CREATE TABLE employees (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            department_id INTEGER,
            salary INTEGER,
            FOREIGN KEY (department_id) REFERENCES departments(id)
        );

        CREATE TABLE projects (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            budget INTEGER
        );

        CREATE TABLE employee_projects (
            employee_id INTEGER,
            project_id INTEGER,
            PRIMARY KEY (employee_id, project_id),
            FOREIGN KEY (employee_id) REFERENCES employees(id),
            FOREIGN KEY (project_id) REFERENCES projects(id)
        );
        """
        )

    def _get_seed_sql_internal(self) -> str:
        return """
        INSERT INTO departments (id, name) VALUES (1, 'Engineering');
        INSERT INTO departments (id, name) VALUES (2, 'HR');
        INSERT INTO departments (id, name) VALUES (3, 'Sales');

        INSERT INTO employees (id, name, department_id, salary) VALUES (1, 'Alice', 1, 90000);
        INSERT INTO employees (id, name, department_id, salary) VALUES (2, 'Bob', 1, 80000);
        INSERT INTO employees (id, name, department_id, salary) VALUES (3, 'Charlie', 2, 60000);
        INSERT INTO employees (id, name, department_id, salary) VALUES (4, 'Diana', 3, 75000);

        INSERT INTO projects (id, name, budget) VALUES (1, 'Platform Revamp', 200000);
        INSERT INTO projects (id, name, budget) VALUES (2, 'AI Initiative', 300000);

        INSERT INTO employee_projects (employee_id, project_id) VALUES (1, 1);
        INSERT INTO employee_projects (employee_id, project_id) VALUES (2, 1);
        INSERT INTO employee_projects (employee_id, project_id) VALUES (1, 2);
        INSERT INTO employee_projects (employee_id, project_id) VALUES (4, 2);
        """

    def _load_data(self) -> None:
        cursor = self._connection.cursor()

        cursor.executemany(
            "INSERT INTO departments (id, name) VALUES (?, ?)",
            [
                (1, "Engineering"),
                (2, "HR"),
                (3, "Sales"),
            ],
        )

        cursor.executemany(
            "INSERT INTO employees (id, name, department_id, salary) VALUES (?, ?, ?, ?)",
            [
                (1, "Alice", 1, 90000),
                (2, "Bob", 1, 80000),
                (3, "Charlie", 2, 60000),
                (4, "Diana", 3, 75000),
            ],
        )

        cursor.executemany(
            "INSERT INTO projects (id, name, budget) VALUES (?, ?, ?)",
            [
                (1, "Platform Revamp", 200000),
                (2, "AI Initiative", 300000),
            ],
        )

        cursor.executemany(
            "INSERT INTO employee_projects (employee_id, project_id) VALUES (?, ?)",
            [
                (1, 1),
                (2, 1),
                (1, 2),
                (4, 2),
            ],
        )

        self._connection.commit()

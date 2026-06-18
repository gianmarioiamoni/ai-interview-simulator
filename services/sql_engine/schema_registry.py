# services/sql_engine/schema_registry.py

from domain.contracts.interview.business_context import BusinessContext
from domain.contracts.question.sql_domain import SqlDomain
from services.sql_engine.schema_definition import SchemaDefinition

_GENERIC_SCHEMA = SchemaDefinition(
    context_key=BusinessContext.GENERIC,
    schema_sql="""
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
""",
    seed_sql="""
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
""",
    domain_tags=(
        SqlDomain.JOIN,
        SqlDomain.GROUP_BY,
        SqlDomain.HAVING,
        SqlDomain.EXISTS,
        SqlDomain.CTE,
        SqlDomain.WINDOW_FUNCTION,
        SqlDomain.CORRELATED_SUBQUERY,
        SqlDomain.TRANSACTION,
    ),
)

_FINTECH_SCHEMA = SchemaDefinition(
    context_key=BusinessContext.FINTECH,
    schema_sql="""
CREATE TABLE customers (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    country TEXT
);

CREATE TABLE accounts (
    id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    account_type TEXT NOT NULL,
    balance REAL NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);

CREATE TABLE transactions (
    id INTEGER PRIMARY KEY,
    account_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    direction TEXT NOT NULL,
    category TEXT,
    transaction_date TEXT NOT NULL,
    FOREIGN KEY (account_id) REFERENCES accounts(id)
);

CREATE TABLE portfolios (
    id INTEGER PRIMARY KEY,
    account_id INTEGER NOT NULL,
    asset TEXT NOT NULL,
    quantity REAL NOT NULL,
    purchase_price REAL NOT NULL,
    FOREIGN KEY (account_id) REFERENCES accounts(id)
);
""",
    seed_sql="""
INSERT INTO customers (id, name, email, country) VALUES (1, 'Alice', 'alice@example.com', 'US');
INSERT INTO customers (id, name, email, country) VALUES (2, 'Bob', 'bob@example.com', 'UK');
INSERT INTO customers (id, name, email, country) VALUES (3, 'Charlie', 'charlie@example.com', 'US');
INSERT INTO customers (id, name, email, country) VALUES (4, 'Diana', 'diana@example.com', 'DE');
INSERT INTO customers (id, name, email, country) VALUES (5, 'Eve', 'eve@example.com', 'US');

INSERT INTO accounts (id, customer_id, account_type, balance, created_at) VALUES (1, 1, 'checking', 5000.00, '2022-01-10');
INSERT INTO accounts (id, customer_id, account_type, balance, created_at) VALUES (2, 1, 'savings', 12000.00, '2022-03-15');
INSERT INTO accounts (id, customer_id, account_type, balance, created_at) VALUES (3, 2, 'checking', 3200.00, '2021-07-01');
INSERT INTO accounts (id, customer_id, account_type, balance, created_at) VALUES (4, 3, 'investment', 45000.00, '2020-11-20');
INSERT INTO accounts (id, customer_id, account_type, balance, created_at) VALUES (5, 4, 'savings', 800.00, '2023-02-28');
INSERT INTO accounts (id, customer_id, account_type, balance, created_at) VALUES (6, 5, 'checking', 0.00, '2023-06-01');

INSERT INTO transactions (id, account_id, amount, direction, category, transaction_date) VALUES (1, 1, 200.00, 'debit', 'food', '2024-01-05');
INSERT INTO transactions (id, account_id, amount, direction, category, transaction_date) VALUES (2, 1, 1500.00, 'credit', 'salary', '2024-01-15');
INSERT INTO transactions (id, account_id, amount, direction, category, transaction_date) VALUES (3, 2, 500.00, 'debit', 'transfer', '2024-01-20');
INSERT INTO transactions (id, account_id, amount, direction, category, transaction_date) VALUES (4, 3, 300.00, 'debit', 'utilities', '2024-01-08');
INSERT INTO transactions (id, account_id, amount, direction, category, transaction_date) VALUES (5, 3, 2000.00, 'credit', 'salary', '2024-01-15');
INSERT INTO transactions (id, account_id, amount, direction, category, transaction_date) VALUES (6, 4, 5000.00, 'debit', 'investment', '2024-01-22');
INSERT INTO transactions (id, account_id, amount, direction, category, transaction_date) VALUES (7, 4, 8000.00, 'credit', 'dividend', '2024-01-31');
INSERT INTO transactions (id, account_id, amount, direction, category, transaction_date) VALUES (8, 5, 50.00, 'debit', 'food', '2024-01-03');
INSERT INTO transactions (id, account_id, amount, direction, category, transaction_date) VALUES (9, 1, 75.00, 'debit', 'transport', '2024-02-01');
INSERT INTO transactions (id, account_id, amount, direction, category, transaction_date) VALUES (10, 6, 100.00, 'debit', 'food', '2024-02-05');

INSERT INTO portfolios (id, account_id, asset, quantity, purchase_price) VALUES (1, 4, 'AAPL', 10.0, 150.00);
INSERT INTO portfolios (id, account_id, asset, quantity, purchase_price) VALUES (2, 4, 'MSFT', 5.0, 300.00);
INSERT INTO portfolios (id, account_id, asset, quantity, purchase_price) VALUES (3, 4, 'GOOG', 2.0, 2500.00);
INSERT INTO portfolios (id, account_id, asset, quantity, purchase_price) VALUES (4, 2, 'AAPL', 3.0, 145.00);
""",
    domain_tags=(
        SqlDomain.JOIN,
        SqlDomain.GROUP_BY,
        SqlDomain.HAVING,
        SqlDomain.WINDOW_FUNCTION,
        SqlDomain.CTE,
        SqlDomain.CORRELATED_SUBQUERY,
        SqlDomain.TRANSACTION,
        SqlDomain.ACID,
        SqlDomain.INDEXING,
        SqlDomain.PERFORMANCE,
    ),
    summary_hint="Fintech schema: customers, accounts, transactions, portfolios.",
)

_REGISTRY: dict[BusinessContext, SchemaDefinition] = {
    BusinessContext.GENERIC: _GENERIC_SCHEMA,
    BusinessContext.FINTECH: _FINTECH_SCHEMA,
}


class SchemaRegistry:
    @staticmethod
    def get(business_context: BusinessContext) -> SchemaDefinition:
        return _REGISTRY.get(business_context, _GENERIC_SCHEMA)

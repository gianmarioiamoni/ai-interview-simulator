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
    vocabulary_hint=(
        "merchant", "settlement", "ledger", "chargeback",
        "reconciliation", "fraud", "compliance", "balance",
        "payment", "transfer", "portfolio", "investment",
    ),
)

_ECOMMERCE_SCHEMA = SchemaDefinition(
    context_key=BusinessContext.ECOMMERCE,
    schema_sql="""
CREATE TABLE customers (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    country TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE categories (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    parent_id INTEGER,
    FOREIGN KEY (parent_id) REFERENCES categories(id)
);

CREATE TABLE products (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    category_id INTEGER NOT NULL,
    price REAL NOT NULL,
    stock_quantity INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (category_id) REFERENCES categories(id)
);

CREATE TABLE orders (
    id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    status TEXT NOT NULL,
    order_date TEXT NOT NULL,
    total_amount REAL NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);

CREATE TABLE order_items (
    id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price REAL NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);
""",
    seed_sql="""
INSERT INTO customers (id, name, email, country, created_at) VALUES (1, 'Alice', 'alice@example.com', 'US', '2022-01-10');
INSERT INTO customers (id, name, email, country, created_at) VALUES (2, 'Bob', 'bob@example.com', 'UK', '2022-03-15');
INSERT INTO customers (id, name, email, country, created_at) VALUES (3, 'Charlie', 'charlie@example.com', 'US', '2021-07-01');
INSERT INTO customers (id, name, email, country, created_at) VALUES (4, 'Diana', 'diana@example.com', 'DE', '2023-02-28');
INSERT INTO customers (id, name, email, country, created_at) VALUES (5, 'Eve', 'eve@example.com', 'US', '2023-06-01');

INSERT INTO categories (id, name, parent_id) VALUES (1, 'Electronics', NULL);
INSERT INTO categories (id, name, parent_id) VALUES (2, 'Clothing', NULL);
INSERT INTO categories (id, name, parent_id) VALUES (3, 'Laptops', 1);
INSERT INTO categories (id, name, parent_id) VALUES (4, 'Phones', 1);
INSERT INTO categories (id, name, parent_id) VALUES (5, 'T-Shirts', 2);

INSERT INTO products (id, name, category_id, price, stock_quantity) VALUES (1, 'Pro Laptop 15', 3, 1299.99, 25);
INSERT INTO products (id, name, category_id, price, stock_quantity) VALUES (2, 'SmartPhone X', 4, 799.00, 50);
INSERT INTO products (id, name, category_id, price, stock_quantity) VALUES (3, 'Wireless Earbuds', 1, 149.99, 100);
INSERT INTO products (id, name, category_id, price, stock_quantity) VALUES (4, 'Cotton T-Shirt', 5, 29.99, 200);
INSERT INTO products (id, name, category_id, price, stock_quantity) VALUES (5, 'Budget Laptop', 3, 499.00, 15);

INSERT INTO orders (id, customer_id, status, order_date, total_amount) VALUES (1, 1, 'delivered', '2024-01-05', 1449.98);
INSERT INTO orders (id, customer_id, status, order_date, total_amount) VALUES (2, 2, 'shipped', '2024-01-10', 799.00);
INSERT INTO orders (id, customer_id, status, order_date, total_amount) VALUES (3, 1, 'pending', '2024-02-01', 149.99);
INSERT INTO orders (id, customer_id, status, order_date, total_amount) VALUES (4, 3, 'delivered', '2024-01-20', 59.98);
INSERT INTO orders (id, customer_id, status, order_date, total_amount) VALUES (5, 4, 'cancelled', '2024-01-25', 799.00);
INSERT INTO orders (id, customer_id, status, order_date, total_amount) VALUES (6, 5, 'delivered', '2024-02-10', 499.00);

INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES (1, 1, 1, 1, 1299.99);
INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES (2, 1, 3, 1, 149.99);
INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES (3, 2, 2, 1, 799.00);
INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES (4, 3, 3, 1, 149.99);
INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES (5, 4, 4, 2, 29.99);
INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES (6, 5, 2, 1, 799.00);
INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES (7, 6, 5, 1, 499.00);
""",
    domain_tags=(
        SqlDomain.JOIN,
        SqlDomain.GROUP_BY,
        SqlDomain.HAVING,
        SqlDomain.EXISTS,
        SqlDomain.CTE,
        SqlDomain.WINDOW_FUNCTION,
        SqlDomain.CORRELATED_SUBQUERY,
        SqlDomain.UNION,
        SqlDomain.INDEXING,
        SqlDomain.PERFORMANCE,
    ),
    summary_hint="E-commerce schema: customers, categories, products, orders, order_items.",
    vocabulary_hint=(
        "inventory", "fulfillment", "warehouse", "sku",
        "returns", "supplier", "shipment", "checkout",
        "cart", "catalog", "discount", "revenue",
    ),
)

_SAAS_SCHEMA = SchemaDefinition(
    context_key=BusinessContext.SAAS,
    schema_sql="""
CREATE TABLE tenants (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    domain TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL
);

CREATE TABLE plans (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    price_monthly REAL NOT NULL,
    max_users INTEGER,
    max_usage_units INTEGER
);

CREATE TABLE subscriptions (
    id INTEGER PRIMARY KEY,
    tenant_id INTEGER NOT NULL,
    plan_id INTEGER NOT NULL,
    status TEXT NOT NULL,
    started_at TEXT NOT NULL,
    expires_at TEXT,
    FOREIGN KEY (tenant_id) REFERENCES tenants(id),
    FOREIGN KEY (plan_id) REFERENCES plans(id)
);

CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    tenant_id INTEGER NOT NULL,
    email TEXT NOT NULL UNIQUE,
    role TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (tenant_id) REFERENCES tenants(id)
);

CREATE TABLE usage_events (
    id INTEGER PRIMARY KEY,
    tenant_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    units INTEGER NOT NULL DEFAULT 1,
    event_date TEXT NOT NULL,
    FOREIGN KEY (tenant_id) REFERENCES tenants(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);
""",
    seed_sql="""
INSERT INTO tenants (id, name, domain, created_at) VALUES (1, 'Acme Corp', 'acme.example.com', '2021-03-01');
INSERT INTO tenants (id, name, domain, created_at) VALUES (2, 'Globex', 'globex.example.com', '2022-06-15');
INSERT INTO tenants (id, name, domain, created_at) VALUES (3, 'Initech', 'initech.example.com', '2023-01-10');
INSERT INTO tenants (id, name, domain, created_at) VALUES (4, 'Umbrella', 'umbrella.example.com', '2023-08-20');

INSERT INTO plans (id, name, price_monthly, max_users, max_usage_units) VALUES (1, 'Starter', 29.00, 5, 1000);
INSERT INTO plans (id, name, price_monthly, max_users, max_usage_units) VALUES (2, 'Growth', 99.00, 25, 10000);
INSERT INTO plans (id, name, price_monthly, max_users, max_usage_units) VALUES (3, 'Enterprise', 499.00, NULL, NULL);

INSERT INTO subscriptions (id, tenant_id, plan_id, status, started_at, expires_at) VALUES (1, 1, 3, 'active', '2021-03-01', NULL);
INSERT INTO subscriptions (id, tenant_id, plan_id, status, started_at, expires_at) VALUES (2, 2, 2, 'active', '2022-06-15', NULL);
INSERT INTO subscriptions (id, tenant_id, plan_id, status, started_at, expires_at) VALUES (3, 3, 1, 'active', '2023-01-10', NULL);
INSERT INTO subscriptions (id, tenant_id, plan_id, status, started_at, expires_at) VALUES (4, 4, 1, 'cancelled', '2023-08-20', '2024-01-01');

INSERT INTO users (id, tenant_id, email, role, created_at) VALUES (1, 1, 'alice@acme.example.com', 'admin', '2021-03-01');
INSERT INTO users (id, tenant_id, email, role, created_at) VALUES (2, 1, 'bob@acme.example.com', 'member', '2021-04-10');
INSERT INTO users (id, tenant_id, email, role, created_at) VALUES (3, 1, 'carol@acme.example.com', 'member', '2022-01-05');
INSERT INTO users (id, tenant_id, email, role, created_at) VALUES (4, 2, 'dave@globex.example.com', 'admin', '2022-06-15');
INSERT INTO users (id, tenant_id, email, role, created_at) VALUES (5, 2, 'eve@globex.example.com', 'member', '2022-07-01');
INSERT INTO users (id, tenant_id, email, role, created_at) VALUES (6, 3, 'frank@initech.example.com', 'admin', '2023-01-10');
INSERT INTO users (id, tenant_id, email, role, created_at) VALUES (7, 4, 'grace@umbrella.example.com', 'admin', '2023-08-20');

INSERT INTO usage_events (id, tenant_id, user_id, event_type, units, event_date) VALUES (1, 1, 1, 'api_call', 50, '2024-01-05');
INSERT INTO usage_events (id, tenant_id, user_id, event_type, units, event_date) VALUES (2, 1, 2, 'api_call', 120, '2024-01-06');
INSERT INTO usage_events (id, tenant_id, user_id, event_type, units, event_date) VALUES (3, 1, 3, 'export', 1, '2024-01-07');
INSERT INTO usage_events (id, tenant_id, user_id, event_type, units, event_date) VALUES (4, 2, 4, 'api_call', 300, '2024-01-05');
INSERT INTO usage_events (id, tenant_id, user_id, event_type, units, event_date) VALUES (5, 2, 5, 'api_call', 200, '2024-01-06');
INSERT INTO usage_events (id, tenant_id, user_id, event_type, units, event_date) VALUES (6, 3, 6, 'api_call', 80, '2024-01-05');
INSERT INTO usage_events (id, tenant_id, user_id, event_type, units, event_date) VALUES (7, 3, 6, 'export', 2, '2024-01-08');
INSERT INTO usage_events (id, tenant_id, user_id, event_type, units, event_date) VALUES (8, 1, 1, 'api_call', 90, '2024-02-01');
INSERT INTO usage_events (id, tenant_id, user_id, event_type, units, event_date) VALUES (9, 2, 4, 'export', 3, '2024-02-03');
INSERT INTO usage_events (id, tenant_id, user_id, event_type, units, event_date) VALUES (10, 4, 7, 'api_call', 10, '2023-12-15');
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
        SqlDomain.INDEXING,
        SqlDomain.PERFORMANCE,
    ),
    summary_hint="SaaS schema: tenants, plans, subscriptions, users, usage_events.",
    vocabulary_hint=(
        "churn", "retention", "engagement", "usage events",
        "MRR", "ARR", "feature adoption", "billing",
        "onboarding", "seat", "tier", "quota",
    ),
)

_HEALTHCARE_SCHEMA = SchemaDefinition(
    context_key=BusinessContext.HEALTHCARE,
    schema_sql="""
CREATE TABLE providers (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    specialty TEXT NOT NULL,
    license_number TEXT NOT NULL UNIQUE
);

CREATE TABLE patients (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    date_of_birth TEXT NOT NULL,
    gender TEXT NOT NULL,
    provider_id INTEGER,
    FOREIGN KEY (provider_id) REFERENCES providers(id)
);

CREATE TABLE appointments (
    id INTEGER PRIMARY KEY,
    patient_id INTEGER NOT NULL,
    provider_id INTEGER NOT NULL,
    appointment_date TEXT NOT NULL,
    status TEXT NOT NULL,
    reason TEXT,
    FOREIGN KEY (patient_id) REFERENCES patients(id),
    FOREIGN KEY (provider_id) REFERENCES providers(id)
);

CREATE TABLE diagnoses (
    id INTEGER PRIMARY KEY,
    patient_id INTEGER NOT NULL,
    appointment_id INTEGER NOT NULL,
    icd_code TEXT NOT NULL,
    description TEXT NOT NULL,
    diagnosed_at TEXT NOT NULL,
    FOREIGN KEY (patient_id) REFERENCES patients(id),
    FOREIGN KEY (appointment_id) REFERENCES appointments(id)
);

CREATE TABLE prescriptions (
    id INTEGER PRIMARY KEY,
    patient_id INTEGER NOT NULL,
    provider_id INTEGER NOT NULL,
    medication TEXT NOT NULL,
    dosage TEXT NOT NULL,
    issued_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    status TEXT NOT NULL,
    FOREIGN KEY (patient_id) REFERENCES patients(id),
    FOREIGN KEY (provider_id) REFERENCES providers(id)
);
""",
    seed_sql="""
INSERT INTO providers (id, name, specialty, license_number) VALUES (1, 'Dr. Alice Chen', 'Cardiology', 'LIC-001');
INSERT INTO providers (id, name, specialty, license_number) VALUES (2, 'Dr. Bob Patel', 'General Practice', 'LIC-002');
INSERT INTO providers (id, name, specialty, license_number) VALUES (3, 'Dr. Carol Smith', 'Neurology', 'LIC-003');
INSERT INTO providers (id, name, specialty, license_number) VALUES (4, 'Dr. David Kim', 'Orthopedics', 'LIC-004');
INSERT INTO providers (id, name, specialty, license_number) VALUES (5, 'Dr. Eve Torres', 'Pediatrics', 'LIC-005');

INSERT INTO patients (id, name, date_of_birth, gender, provider_id) VALUES (1, 'James Wilson', '1980-03-15', 'M', 2);
INSERT INTO patients (id, name, date_of_birth, gender, provider_id) VALUES (2, 'Maria Garcia', '1975-07-22', 'F', 1);
INSERT INTO patients (id, name, date_of_birth, gender, provider_id) VALUES (3, 'Tom Brown', '1990-11-08', 'M', 2);
INSERT INTO patients (id, name, date_of_birth, gender, provider_id) VALUES (4, 'Sarah Lee', '1968-01-30', 'F', 3);
INSERT INTO patients (id, name, date_of_birth, gender, provider_id) VALUES (5, 'Chris Davis', '2000-05-14', 'M', 5);
INSERT INTO patients (id, name, date_of_birth, gender, provider_id) VALUES (6, 'Anna White', '1955-09-03', 'F', 1);
INSERT INTO patients (id, name, date_of_birth, gender, provider_id) VALUES (7, 'Mike Johnson', '1985-12-19', 'M', 4);
INSERT INTO patients (id, name, date_of_birth, gender, provider_id) VALUES (8, 'Lucy Martinez', '1995-06-27', 'F', 2);

INSERT INTO appointments (id, patient_id, provider_id, appointment_date, status, reason) VALUES (1, 1, 2, '2024-01-10', 'completed', 'Annual checkup');
INSERT INTO appointments (id, patient_id, provider_id, appointment_date, status, reason) VALUES (2, 2, 1, '2024-01-12', 'completed', 'Chest pain evaluation');
INSERT INTO appointments (id, patient_id, provider_id, appointment_date, status, reason) VALUES (3, 3, 2, '2024-01-15', 'no_show', 'Follow-up');
INSERT INTO appointments (id, patient_id, provider_id, appointment_date, status, reason) VALUES (4, 4, 3, '2024-01-18', 'completed', 'Headache assessment');
INSERT INTO appointments (id, patient_id, provider_id, appointment_date, status, reason) VALUES (5, 5, 5, '2024-01-20', 'completed', 'Vaccination');
INSERT INTO appointments (id, patient_id, provider_id, appointment_date, status, reason) VALUES (6, 6, 1, '2024-01-22', 'cancelled', 'Arrhythmia checkup');
INSERT INTO appointments (id, patient_id, provider_id, appointment_date, status, reason) VALUES (7, 7, 4, '2024-01-25', 'completed', 'Knee pain');
INSERT INTO appointments (id, patient_id, provider_id, appointment_date, status, reason) VALUES (8, 8, 2, '2024-02-01', 'completed', 'General consultation');
INSERT INTO appointments (id, patient_id, provider_id, appointment_date, status, reason) VALUES (9, 1, 2, '2024-02-05', 'completed', 'Blood pressure review');
INSERT INTO appointments (id, patient_id, provider_id, appointment_date, status, reason) VALUES (10, 2, 1, '2024-02-10', 'scheduled', 'Stress test');

INSERT INTO diagnoses (id, patient_id, appointment_id, icd_code, description, diagnosed_at) VALUES (1, 1, 1, 'I10', 'Essential hypertension', '2024-01-10');
INSERT INTO diagnoses (id, patient_id, appointment_id, icd_code, description, diagnosed_at) VALUES (2, 2, 2, 'I20.9', 'Unstable angina', '2024-01-12');
INSERT INTO diagnoses (id, patient_id, appointment_id, icd_code, description, diagnosed_at) VALUES (3, 4, 4, 'G43.909', 'Migraine', '2024-01-18');
INSERT INTO diagnoses (id, patient_id, appointment_id, icd_code, description, diagnosed_at) VALUES (4, 5, 5, 'Z23', 'Immunization encounter', '2024-01-20');
INSERT INTO diagnoses (id, patient_id, appointment_id, icd_code, description, diagnosed_at) VALUES (5, 7, 7, 'M17.11', 'Osteoarthritis of right knee', '2024-01-25');
INSERT INTO diagnoses (id, patient_id, appointment_id, icd_code, description, diagnosed_at) VALUES (6, 8, 8, 'J06.9', 'Upper respiratory infection', '2024-02-01');
INSERT INTO diagnoses (id, patient_id, appointment_id, icd_code, description, diagnosed_at) VALUES (7, 1, 9, 'I10', 'Essential hypertension', '2024-02-05');
INSERT INTO diagnoses (id, patient_id, appointment_id, icd_code, description, diagnosed_at) VALUES (8, 2, 2, 'Z82.49', 'Family history of ischemic heart disease', '2024-01-12');

INSERT INTO prescriptions (id, patient_id, provider_id, medication, dosage, issued_at, expires_at, status) VALUES (1, 1, 2, 'Lisinopril', '10mg daily', '2024-01-10', '2025-01-10', 'active');
INSERT INTO prescriptions (id, patient_id, provider_id, medication, dosage, issued_at, expires_at, status) VALUES (2, 2, 1, 'Nitroglycerin', '0.4mg sublingual', '2024-01-12', '2025-01-12', 'active');
INSERT INTO prescriptions (id, patient_id, provider_id, medication, dosage, issued_at, expires_at, status) VALUES (3, 4, 3, 'Sumatriptan', '50mg as needed', '2024-01-18', '2024-07-18', 'expired');
INSERT INTO prescriptions (id, patient_id, provider_id, medication, dosage, issued_at, expires_at, status) VALUES (4, 7, 4, 'Ibuprofen', '400mg three times daily', '2024-01-25', '2024-04-25', 'active');
INSERT INTO prescriptions (id, patient_id, provider_id, medication, dosage, issued_at, expires_at, status) VALUES (5, 8, 2, 'Amoxicillin', '500mg three times daily', '2024-02-01', '2024-02-15', 'completed');
INSERT INTO prescriptions (id, patient_id, provider_id, medication, dosage, issued_at, expires_at, status) VALUES (6, 1, 2, 'Atorvastatin', '20mg nightly', '2024-02-05', '2025-02-05', 'active');
INSERT INTO prescriptions (id, patient_id, provider_id, medication, dosage, issued_at, expires_at, status) VALUES (7, 6, 1, 'Metoprolol', '25mg twice daily', '2023-06-01', '2024-06-01', 'active');
INSERT INTO prescriptions (id, patient_id, provider_id, medication, dosage, issued_at, expires_at, status) VALUES (8, 3, 2, 'Omeprazole', '20mg daily', '2023-11-15', '2024-02-15', 'expired');
""",
    domain_tags=(
        SqlDomain.JOIN,
        SqlDomain.GROUP_BY,
        SqlDomain.HAVING,
        SqlDomain.EXISTS,
        SqlDomain.CTE,
        SqlDomain.WINDOW_FUNCTION,
        SqlDomain.CORRELATED_SUBQUERY,
        SqlDomain.INDEXING,
        SqlDomain.PERFORMANCE,
    ),
    summary_hint="Healthcare schema: providers, patients, appointments, diagnoses, prescriptions.",
    vocabulary_hint=(
        "patient", "diagnosis", "prescription", "provider", "appointment",
        "treatment", "referral", "care plan", "clinical workflow",
        "encounter", "laboratory", "healthcare",
    ),
)

_REGISTRY: dict[BusinessContext, SchemaDefinition] = {
    BusinessContext.GENERIC: _GENERIC_SCHEMA,
    BusinessContext.FINTECH: _FINTECH_SCHEMA,
    BusinessContext.ECOMMERCE: _ECOMMERCE_SCHEMA,
    BusinessContext.SAAS: _SAAS_SCHEMA,
    BusinessContext.HEALTHCARE: _HEALTHCARE_SCHEMA,
}


class SchemaRegistry:
    @staticmethod
    def get(business_context: BusinessContext) -> SchemaDefinition:
        return _REGISTRY.get(business_context, _GENERIC_SCHEMA)

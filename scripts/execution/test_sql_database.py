# scripts/test_sql_database.py

from services.sql_engine.sql_database import SQLDatabase


def main():

    db = SQLDatabase()

    print("\n=== SCHEMA ===")
    print(db.get_schema_sql())

    print("\n=== SEED ===")
    print(db.get_seed_sql())

    # -------------------------------------------------
    # TEST REALE (importantissimo)
    # -------------------------------------------------

    conn = db.get_fresh_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM employees")
    rows = cursor.fetchall()

    print("\n=== QUERY TEST ===")
    print(rows)


if __name__ == "__main__":
    main()


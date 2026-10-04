import re
import psycopg2
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

BLOCKED = r"\b(drop|delete|update|insert|alter|truncate|create|grant|revoke|copy)\b"

def is_safe_query(sql: str):
    cleaned = re.sub(r"--.*?$|/\*.*?\*/", "", sql, flags=re.S | re.M).strip().rstrip(";").strip()
    if ";" in cleaned:
        return False, "Multiple statements are not allowed."
    if not re.match(r"^(select|with)\b", cleaned, re.I):
        return False, "Only SELECT queries are allowed."
    if re.search(BLOCKED, cleaned, re.I):
        return False, "Query contains a blocked keyword."
    return True, "OK"

def get_connection():
    conn = psycopg2.connect(
        os.getenv("DATABASE_URL"),
        sslmode="require"
    )
    return conn

def init_db():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS employees (
                id SERIAL PRIMARY KEY,
                name TEXT,
                department TEXT,
                salary INTEGER,
                city TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sales (
                id SERIAL PRIMARY KEY,
                employee_id INTEGER,
                product TEXT,
                amount INTEGER,
                sale_date DATE
            )
        """)
        cursor.execute("SELECT COUNT(*) FROM employees")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO employees (name, department, salary, city) VALUES
                ('Alice', 'Engineering', 90000, 'Hyderabad'),
                ('Bob', 'Marketing', 60000, 'Mumbai'),
                ('Charlie', 'Engineering', 95000, 'Hyderabad'),
                ('Diana', 'HR', 50000, 'Delhi'),
                ('Eve', 'Marketing', 65000, 'Bangalore')
            """)
        cursor.execute("SELECT COUNT(*) FROM sales")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO sales (employee_id, product, amount, sale_date) VALUES
                (1, 'Laptop', 120000, '2024-01-15'),
                (2, 'Phone', 45000, '2024-01-20'),
                (1, 'Tablet', 30000, '2024-02-10'),
                (3, 'Laptop', 120000, '2024-02-15'),
                (5, 'Phone', 45000, '2024-03-01')
            """)
        conn.commit()
        cursor.close()
        conn.close()
        print("✅ Connected to Supabase PostgreSQL!")
    except Exception as e:
        print(f"❌ Database error: {e}")

def run_query(sql):
    ok, msg = is_safe_query(sql)
    if not ok:
        return None, f"🚫 Blocked for safety: {msg}"
    try:
        conn = get_connection()
        df = pd.read_sql_query(sql, conn)
        conn.close()
        return df, None
    except Exception as e:
        return None, str(e)

def get_schema():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
        """)
        tables = cursor.fetchall()
        schema = ""
        for table in tables:
            table_name = table[0]
            cursor.execute(f"""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = '{table_name}'
                AND table_schema = 'public'
            """)
            columns = cursor.fetchall()
            cols = ", ".join([f"{col[0]} ({col[1]})" for col in columns])
            schema += f"Table: {table_name} → Columns: {cols}\n"
        cursor.close()
        conn.close()
        return schema
    except Exception as e:
        return f"Schema error: {str(e)}"

def load_csv_to_db(df, table_name):
    try:
        conn = get_connection()
        df.to_sql(table_name, conn, if_exists='replace', index=False)
        conn.close()
    except Exception as e:
        print(f"Error loading CSV: {e}")


HARD_BLOCK = r"\b(drop\s+(database|schema|role|user)|alter\s+(role|user|database)|grant|revoke|copy|create\s+(role|user|extension))\b"


def is_confirmable(sql: str):
    cleaned = re.sub(r"--.*?$|/\*.*?\*/", "", sql, flags=re.S | re.M).strip()
    if not cleaned:
        return False
    return not re.search(HARD_BLOCK, cleaned, re.I)


def run_any_query(sql):
    """Runs any SQL type. Only called after the user clicks Confirm."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(sql)
        if cursor.description:
            df = pd.DataFrame(cursor.fetchall(), columns=[d[0] for d in cursor.description])
        else:
            n = cursor.rowcount
            msg = "Query executed successfully ✅" if n < 0 else f"Query executed successfully ✅ ({n} rows affected)"
            df = pd.DataFrame([{"message": msg}])
        conn.commit()
        cursor.close()
        return df, None
    except Exception as e:
        return None, str(e)
    finally:
        if conn:
            conn.close()

import psycopg2
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

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
    try:
        conn = get_connection()
        cursor = conn.cursor()
        if sql.strip().upper().startswith('SELECT'):
            df = pd.read_sql_query(sql, conn)
        else:
            cursor.execute(sql)
            conn.commit()
            df = pd.DataFrame([{"message": "Query executed successfully ✅"}])
        cursor.close()
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
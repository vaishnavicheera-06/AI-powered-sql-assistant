import time
import streamlit as st
import pandas as pd
from database import run_query, get_schema
from llm import generate_sql

st.set_page_config(page_title="Accuracy Test", page_icon="📊", layout="wide")

st.title("📊 Accuracy Test")
st.caption(
    "Runs 20 test questions. A question counts as correct when the AI's SQL "
    "returns the same result as the known-correct SQL."
)

TESTS = [
    ("List all employees", "SELECT * FROM employees"),
    ("Show employees in Engineering", "SELECT * FROM employees WHERE department = 'Engineering'"),
    ("Show employees from Hyderabad", "SELECT * FROM employees WHERE city = 'Hyderabad'"),
    ("Top 3 highest paid employees", "SELECT * FROM employees ORDER BY salary DESC LIMIT 3"),
    ("How many employees are there", "SELECT COUNT(*) FROM employees"),
    ("What is the average salary of all employees", "SELECT AVG(salary) FROM employees"),
    ("Average salary by department", "SELECT department, AVG(salary) FROM employees GROUP BY department"),
    ("What is the total sales amount", "SELECT SUM(amount) FROM sales"),
    ("Total sales by product", "SELECT product, SUM(amount) FROM sales GROUP BY product"),
    ("Employees who never made sales", "SELECT * FROM employees WHERE id NOT IN (SELECT employee_id FROM sales)"),
    ("Show the highest paid employee", "SELECT * FROM employees ORDER BY salary DESC LIMIT 1"),
    ("Show the lowest paid employee", "SELECT * FROM employees ORDER BY salary ASC LIMIT 1"),
    ("Number of employees in each department", "SELECT department, COUNT(*) FROM employees GROUP BY department"),
    ("Show names and salaries of employees earning more than 60000", "SELECT name, salary FROM employees WHERE salary > 60000"),
    ("Total sales amount for each employee name", "SELECT e.name, SUM(s.amount) FROM employees e JOIN sales s ON e.id = s.employee_id GROUP BY e.name"),
    ("Show sales made in February 2024", "SELECT * FROM sales WHERE sale_date >= '2024-02-01' AND sale_date < '2024-03-01'"),
    ("Show sales with amount greater than 40000", "SELECT * FROM sales WHERE amount > 40000"),
    ("Show each employee name with the products they sold", "SELECT e.name, s.product FROM employees e JOIN sales s ON e.id = s.employee_id"),
    ("Show employees in Marketing earning more than 62000", "SELECT * FROM employees WHERE department = 'Marketing' AND salary > 62000"),
    ("Show all sales of Laptop", "SELECT * FROM sales WHERE product = 'Laptop'"),
]


def normalize(df):
    """Turn a result table into a sorted list of rows so order and column names don't matter."""
    rows = []
    for row in df.itertuples(index=False):
        vals = []
        for v in row:
            try:
                vals.append(str(round(float(v), 2)))
            except (TypeError, ValueError):
                vals.append(str(v).strip().lower())
        rows.append(tuple(vals))
    return sorted(rows)


if st.button("▶ Run accuracy test"):
    schema = get_schema()
    results = []
    progress = st.progress(0)
    status = st.empty()

    for i, (question, expected_sql) in enumerate(TESTS):
        status.write(f"Testing {i + 1}/{len(TESTS)}: {question}")
        try:
            ai_sql = generate_sql(question, schema)
            expected_df, expected_err = run_query(expected_sql)
            ai_df, ai_err = run_query(ai_sql)
            if expected_err or ai_err:
                correct = False
            else:
                correct = normalize(expected_df) == normalize(ai_df)
        except Exception as e:
            ai_sql = f"Error: {e}"
            correct = False

        results.append({
            "Question": question,
            "Correct SQL": expected_sql,
            "AI SQL": ai_sql,
            "Result": "✅ Correct" if correct else "❌ Wrong",
        })
        progress.progress((i + 1) / len(TESTS))
        time.sleep(1)

    status.empty()
    passed = sum(1 for r in results if r["Result"].startswith("✅"))
    total = len(results)

    st.metric("Accuracy", f"{passed}/{total}  =  {round(100 * passed / total)}%")
    st.dataframe(pd.DataFrame(results), use_container_width=True)

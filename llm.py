import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def generate_sql(user_question, schema):
    prompt = f"""You are an expert SQL assistant.
Convert the user question into a valid PostgreSQL SQL query.
Rules:
- Return ONLY ONE single SQL statement
- No explanation, no markdown, no backticks, no semicolon
- Use exact table and column names from schema
- Never use BEGIN, COMMIT, TRANSACTION
- For delete duplicates, target only ONE table at a time
- Use PostgreSQL syntax (TO_CHAR, NOW(), SERIAL, etc)

Schema:
{schema}

User Question: {user_question}

SQL Query:"""
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    sql = response.choices[0].message.content.strip()

    lines = sql.split('\n')
    first_statement = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if first_statement and line.upper().startswith(('SELECT', 'DELETE', 'UPDATE', 'INSERT', 'CREATE', 'DROP', 'ALTER')):
            break
        first_statement.append(line)

    sql = ' '.join(first_statement).strip().rstrip(';')
    return sql

def fix_sql(user_question, schema, broken_sql, error):
    prompt = f"""Fix this PostgreSQL query that failed.
Return ONLY ONE corrected SQL statement.
No explanation. No markdown. No backticks. No semicolon.
Never return multiple statements.
Never use BEGIN, COMMIT, TRANSACTION.
Use PostgreSQL syntax only.

Schema:
{schema}

User Question: {user_question}
Broken SQL: {broken_sql}
Error: {error}

Fixed SQL:"""
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    sql = response.choices[0].message.content.strip()

    lines = sql.split('\n')
    first_statement = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if first_statement and line.upper().startswith(('SELECT', 'DELETE', 'UPDATE', 'INSERT', 'CREATE', 'DROP', 'ALTER')):
            break
        first_statement.append(line)

    sql = ' '.join(first_statement).strip().rstrip(';')
    return sql

def generate_insight(question, sql, result_df):
    prompt = f"""User asked: {question}
SQL used: {sql}
Result: {result_df.to_string()}

Give a 2-3 line simple insight from this result in plain English."""
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    return response.choices[0].message.content.strip()

def explain_sql(sql):
    prompt = f"""Explain this SQL query in simple English line by line.
Be clear and beginner friendly.

SQL Query:
{sql}

Explanation:"""
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    return response.choices[0].message.content.strip()
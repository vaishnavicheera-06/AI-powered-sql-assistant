import html
import datetime
import decimal
import streamlit as st
import pandas as pd
from database import (
    init_db, run_query, run_any_query, is_confirmable,
    is_safe_query, get_schema, load_csv_to_db
)
from llm import generate_sql, fix_sql, generate_insight, explain_sql, explain_query_short

init_db()

st.set_page_config(
    page_title="SQL Query Assistant",
    page_icon="🗄️",
    layout="wide"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background: linear-gradient(135deg, #0f1117 0%, #1a1d2e 100%); }
    .hero { text-align: center; padding: 3rem 0 2rem 0; }
    .hero h1 {
        font-size: 3rem; font-weight: 700;
        background: linear-gradient(90deg, #6C63FF, #48C9B0);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .hero p { color: #8892a4; font-size: 1.1rem; }
    .card {
        background: #1e2130; border: 1px solid #2d3148;
        border-radius: 12px; padding: 1.5rem; margin-bottom: 1rem;
    }
    .card-title {
        color: #6C63FF; font-size: 0.85rem; font-weight: 600;
        text-transform: uppercase; letter-spacing: 1px; margin-bottom: 0.75rem;
    }
    .sql-box {
        background: #12141f; border: 1px solid #2d3148;
        border-left: 3px solid #6C63FF; border-radius: 8px;
        padding: 1rem; font-family: 'JetBrains Mono', monospace;
        color: #e2e8f0; font-size: 0.9rem; white-space: pre-wrap;
    }
    .insight-box {
        background: linear-gradient(135deg, #1a2744, #1e2130);
        border: 1px solid #2d4a7a; border-left: 3px solid #48C9B0;
        border-radius: 8px; padding: 1rem 1.5rem;
        color: #cbd5e1; font-size: 0.95rem; line-height: 1.6;
        white-space: pre-wrap;
    }
    .explain-box {
        background: linear-gradient(135deg, #1a2a1a, #1e2130);
        border: 1px solid #2d4a2d; border-left: 3px solid #48FF90;
        border-radius: 8px; padding: 1rem 1.5rem;
        color: #cbd5e1; font-size: 0.95rem; line-height: 1.6;
    }
    .stat-chip {
        display: inline-block; background: #2d3148;
        border-radius: 20px; padding: 4px 12px;
        font-size: 0.8rem; color: #8892a4; margin-right: 8px;
    }
    .history-item {
        background: #12141f; border: 1px solid #2d3148;
        border-radius: 8px; padding: 0.75rem; margin-bottom: 0.5rem;
        font-size: 0.85rem; color: #8892a4;
    }
    .stButton > button {
        background: linear-gradient(90deg, #6C63FF, #48C9B0);
        color: white; border: none; border-radius: 8px;
        padding: 0.6rem 2rem; font-weight: 600; font-size: 1rem;
        width: 100%;
    }
    .clear-btn > button {
        background: #2d3148 !important;
        color: #8892a4 !important;
    }
    .stTextInput > div > div > input {
        background: #1e2130; border: 1px solid #2d3148;
        border-radius: 8px; color: #e2e8f0; font-size: 1rem;
    }
    .stTextInput > div > div > input:focus {
        border-color: #6C63FF;
        box-shadow: 0 0 0 2px rgba(108,99,255,0.2);
    }
</style>
""", unsafe_allow_html=True)

# Session state
if "history" not in st.session_state:
    st.session_state.history = []
if "query_input" not in st.session_state:
    st.session_state.query_input = ""
if "pending_sql" not in st.session_state:
    st.session_state.pending_sql = None
if "write_result" not in st.session_state:
    st.session_state.write_result = None


def clear_text():
    st.session_state.query_input = ""


def reset_conversation():
    st.session_state.history = []
    st.session_state.query_input = ""
    st.session_state.pending_sql = None
    st.session_state.write_result = None


def build_contextual_question(question):
    """Adds the last 2 successful questions + SQL so follow-ups work."""
    recent = st.session_state.history[-2:]
    if not recent:
        return question
    context = "\n".join(
        f"- Earlier question: {h['question']}\n  Earlier SQL: {h['sql']}"
        for h in recent
    )
    return f"""Conversation so far:
{context}

If the new question refers to earlier results (words like "them", "those", "it", "only", "also", "sort them", "now"), modify the most recent SQL to answer it. If it is a completely new question, ignore the conversation.

New question: {question}"""


def show_query_explanation(sql):
    """Short plain-English explanation + read-only badge under the generated SQL."""
    with st.spinner("📝 Explaining query..."):
        text = explain_query_short(sql)
    if text:
        st.markdown(f'''
        <div class="card">
            <div class="card-title">📝 What this query does</div>
            <div class="insight-box">{html.escape(text)}</div>
        </div>
        ''', unsafe_allow_html=True)
    safe, _ = is_safe_query(sql)
    if safe:
        st.success("🔒 Read-only query — safe to execute")


def chart_title(text):
    st.markdown(f'<div class="card"><div class="card-title">{text}</div></div>', unsafe_allow_html=True)


def prepare_for_chart(df):
    """Postgres AVG/SUM often return Decimal; convert those columns to float for charting."""
    d = df.copy()
    for c in d.columns:
        if pd.api.types.is_object_dtype(d[c]):
            vals = d[c].dropna()
            if len(vals) > 0 and all(isinstance(v, decimal.Decimal) for v in vals):
                d[c] = d[c].astype(float)
    return d


def is_date_col(series):
    if pd.api.types.is_datetime64_any_dtype(series):
        return True
    vals = series.dropna()
    return len(vals) > 0 and all(isinstance(v, datetime.date) for v in vals)


def show_smart_chart(df):
    """Chooses the visualization from the shape of the result."""
    if df.empty:
        return
    d = prepare_for_chart(df)
    n_rows, n_cols = d.shape

    # numeric columns, ignoring id columns
    num_cols = [
        c for c in d.select_dtypes(include="number").columns
        if not (str(c).lower() == "id" or str(c).lower().endswith("_id"))
    ]
    if not num_cols:
        return

    # Single number -> KPI card
    if n_rows == 1 and n_cols == 1:
        val = d.iloc[0, 0]
        try:
            f = float(val)
            text = f"{f:,.0f}" if f.is_integer() else f"{f:,.2f}"
        except (TypeError, ValueError):
            text = str(val)
        chart_title("🔢 Key figure")
        st.metric(label=str(d.columns[0]), value=text)
        return

    # Single row with several values -> the table is enough
    if n_rows == 1:
        return

    if n_rows > 50:
        st.caption("📊 Chart skipped: too many rows to show clearly.")
        return

    date_cols = [c for c in d.columns if is_date_col(d[c])]
    time_like = [
        c for c in num_cols
        if any(k in str(c).lower() for k in ("month", "year", "week", "day"))
    ]
    text_cols = [
        c for c in d.columns
        if c not in date_cols and not pd.api.types.is_numeric_dtype(d[c])
    ]

    try:
        if date_cols:
            x = date_cols[0]
            d[x] = pd.to_datetime(d[x])
            chart_df = d.sort_values(x).set_index(x)[num_cols]
            chart_title("📈 Line chart · trend over time")
            st.line_chart(chart_df, use_container_width=True)
        elif time_like:
            x = time_like[0]
            y = [c for c in num_cols if c != x]
            if not y:
                return
            chart_df = d.sort_values(x).set_index(x)[y]
            chart_title("📈 Line chart · trend over time")
            st.line_chart(chart_df, use_container_width=True)
        elif text_cols:
            x = text_cols[0]
            chart_df = d.set_index(x)[num_cols]
            looks_like_time = (
                any(k in str(x).lower() for k in ("month", "date", "year", "week", "day", "time"))
                or d[x].astype(str).str.match(r"^\d{4}-\d{2}(-\d{2})?$").all()
            )
            if looks_like_time:
                chart_df = chart_df.sort_index()
                chart_title("📈 Line chart · trend over time")
                st.line_chart(chart_df, use_container_width=True)
            else:
                chart_title("📊 Bar chart · comparison")
                st.bar_chart(chart_df,

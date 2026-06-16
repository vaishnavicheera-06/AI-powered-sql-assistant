import streamlit as st
import pandas as pd
from database import init_db, run_query, get_schema, load_csv_to_db
from llm import generate_sql, fix_sql, generate_insight, explain_sql

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
if "clear_input" not in st.session_state:
    st.session_state.clear_input = False

# Hero
st.markdown("""
<div class="hero">
    <h1>🗄️ SQL Query Assistant</h1>
    <p>Ask anything in plain English — get instant SQL queries, results & insights</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### 📋 Database Schema")
    st.code(get_schema(), language="sql")

    st.markdown("---")
    st.markdown("### 📁 Upload Your CSV")
    uploaded_file = st.file_uploader("Upload CSV to query", type=["csv"])
    if uploaded_file:
        df_upload = pd.read_csv(uploaded_file)
        table_name = uploaded_file.name.replace(".csv", "").replace(" ", "_").lower()
        load_csv_to_db(df_upload, table_name)
        st.success(f"✅ Loaded as table: `{table_name}`")

    st.markdown("---")
    st.markdown("### 💡 Example Questions")
    examples = [
        "Show all employees in Engineering",
        "Top 3 highest paid employees",
        "Total sales by product",
        "Employees who never made sales",
        "Average salary by department",
        "Show monthly sales trend"
    ]
    for ex in examples:
        st.markdown(f"• *{ex}*")

    st.markdown("---")
    if st.session_state.history:
        st.markdown("### 🕐 Query History")
        for i, item in enumerate(reversed(st.session_state.history[-5:])):
            st.markdown(f'<div class="history-item">❓ {item["question"]}</div>', unsafe_allow_html=True)

    st.caption("Built with Streamlit + Groq LLaMA3 + SQLite")

# Tabs
tab1, tab2 = st.tabs(["🔍 Query Database", "📖 Explain SQL"])

# Tab 1 — Query
with tab1:
    col1, col2, col3 = st.columns([5, 1, 1])
    with col1:
        default_val = "" if st.session_state.clear_input else None
        user_question = st.text_input(
            "",
            placeholder="e.g. Show employees with salary above 70000 ordered by department",
            label_visibility="collapsed",
            key="query_input",
            value="" if st.session_state.clear_input else st.session_state.get("query_input", "")
        )
        st.session_state.clear_input = False
    with col2:
        run = st.button("▶ Run", key="run_btn")
    with col3:
        st.markdown('<div class="clear-btn">', unsafe_allow_html=True)
        clear = st.button("🗑️ Clear", key="clear_btn")
        st.markdown('</div>', unsafe_allow_html=True)

    if clear:
        st.session_state.clear_input = True
        st.rerun()

    if run:
        if user_question.strip() == "":
            st.warning("Please enter a question.")
        else:
            with st.spinner("🤖 Generating SQL..."):
                schema = get_schema()
                sql = generate_sql(user_question, schema)

            st.markdown('<div class="card"><div class="card-title">⚡ Generated SQL</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="sql-box">{sql}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

            df, error = run_query(sql)

            if error:
                with st.spinner("🔧 Auto-fixing SQL..."):
                    sql = fix_sql(user_question, schema, sql, error)
                st.markdown('<div class="card"><div class="card-title">🔧 Fixed SQL</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="sql-box">{sql}</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
                df, error = run_query(sql)

            if error:
                st.error(f"❌ Could not fix query: {error}")
            else:
                rows, cols_count = df.shape
                st.markdown(f'''
                <div class="card">
                    <div class="card-title">📊 Query Results</div>
                    <span class="stat-chip">{rows} rows</span>
                    <span class="stat-chip">{cols_count} columns</span>
                </div>
                ''', unsafe_allow_html=True)
                st.dataframe(df, use_container_width=True)

                st.download_button(
                    label="⬇️ Download Results as CSV",
                    data=df.to_csv(index=False),
                    file_name="query_results.csv",
                    mime="text/csv"
                )

                if not df.empty:
                    numeric_cols = df.select_dtypes(include='number').columns.tolist()
                    non_numeric_cols = df.select_dtypes(exclude='number').columns.tolist()
                    if len(numeric_cols) > 0 and len(non_numeric_cols) > 0:
                        st.markdown('<div class="card"><div class="card-title">📈 Chart</div></div>', unsafe_allow_html=True)
                        try:
                            chart_df = df.set_index(non_numeric_cols[0])[numeric_cols]
                            st.bar_chart(chart_df, use_container_width=True)
                        except Exception:
                            pass

                with st.spinner("💡 Generating insight..."):
                    insight = generate_insight(user_question, sql, df)
                st.markdown(f'''
                <div class="card">
                    <div class="card-title">💡 AI Insight</div>
                    <div class="insight-box">{insight}</div>
                </div>
                ''', unsafe_allow_html=True)

                st.session_state.history.append({
                    "question": user_question,
                    "sql": sql
                })

# Tab 2 — Explain SQL
with tab2:
    st.markdown("### Paste any SQL query to understand what it does")
    sql_to_explain = st.text_area(
        "",
        placeholder="SELECT e.name, SUM(s.amount) FROM employees e JOIN sales s ON e.id = s.employee_id GROUP BY e.name ORDER BY SUM(s.amount) DESC",
        height=150,
        label_visibility="collapsed"
    )
    if st.button("📖 Explain This Query", key="explain_btn"):
        if sql_to_explain.strip() == "":
            st.warning("Please paste a SQL query.")
        else:
            with st.spinner("📖 Explaining..."):
                explanation = explain_sql(sql_to_explain)
            st.markdown(f'''
            <div class="card">
                <div class="card-title">📖 Explanation</div>
                <div class="explain-box">{explanation}</div>
            </div>
            ''', unsafe_allow_html=True)
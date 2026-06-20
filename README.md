# 🗄️ AI-Powered SQL Query Assistant

An intelligent SQL assistant that converts plain English questions into PostgreSQL queries, executes them in real-time, and provides AI-generated insights — built with Python, Streamlit, Groq LLaMA3, and Supabase.

## 🔴 Live Demo
👉 [ai-powered-sql-assistant-xphgnwyij2pcnebdxjfvce.streamlit.app](https://ai-powered-sql-assistant-xphgnwyij2pcnebdxjfvce.streamlit.app)

## ✨ Features

- 🤖 **Natural Language to SQL** — Ask questions in plain English, get PostgreSQL queries instantly
- 🔧 **Auto SQL Error Correction** — If a query fails, AI automatically fixes it silently
- 📊 **Real-time Results** — Query results displayed as interactive tables with auto charts
- 💡 **AI Insights** — 2-3 line plain English summary of every query result
- 📖 **SQL Explainer** — Paste any SQL query and get line-by-line explanation
- 📁 **CSV Upload** — Upload any CSV file and query it instantly
- ⬇️ **Download Results** — Export any query result as CSV
- 🕐 **Query History** — Last 5 queries saved in sidebar

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| Python | Core language |
| Streamlit | Frontend UI |
| Groq API (LLaMA3 70b) | NL2SQL generation |
| PostgreSQL | Database |
| Supabase | Cloud database hosting |
| Pandas | Data processing |
| Prompt Engineering | AI accuracy optimization |

## 📁 Project Structure

```
ai-powered-sql-assistant/
├── app.py          # Streamlit frontend
├── database.py     # PostgreSQL connection via Supabase
├── llm.py          # Groq AI integration
├── requirements.txt
├── .env            # API keys (not pushed)
└── .gitignore
```

## 🚀 How It Works

```
User types question in English
        ↓
Groq LLaMA3 generates PostgreSQL query
        ↓
Query runs on Supabase PostgreSQL
        ↓
If error → AI auto-fixes silently
        ↓
Result table + Auto chart displayed
        ↓
AI generates 2-3 line insight
```

## 💻 Run Locally

```bash
git clone https://github.com/vaishnavicheera-06/AI-powered-sql-assistant
cd AI-powered-sql-assistant
pip install -r requirements.txt
```

Create `.env` file:
```
GROQ_API_KEY=your_groq_api_key
DATABASE_URL=your_supabase_postgresql_url
```

Run:
```bash
streamlit run app.py
```

## 📊 Sample Queries

- *Show all employees in Engineering department*
- *Top 3 employees by salary*
- *Show total sales by product*
- *Employees who never made any sales*
- *Rank employees by salary using ROW_NUMBER*
- *Show running total of sales by date*
- *Employees earning more than average salary*

## 👩‍💻 Author

**Vaishnavi Cheera**
- GitHub: [@vaishnavicheera-06](https://github.com/vaishnavicheera-06)
- LinkedIn: [vaishnavi-cheera](https://linkedin.com/in/vaishnavi-cheera)

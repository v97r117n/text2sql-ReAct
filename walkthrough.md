# EduGuard — School Dropout Prediction Dashboard

## What Was Built

A full-stack web dashboard for school dropout prediction with an AI chatbot, built on the text2sql framework with local Qwen 3.5 via Ollama.

### Architecture

```
webapp/
├── app.py              ← Flask backend (APIs: chat, students, stats)
└── static/
    ├── index.html       ← 3-view SPA (Dashboard, Students, Chat)
    ├── style.css        ← Premium dark-mode design
    └── app.js           ← All frontend logic
```

Backend changes:
- [agent.py](file:///Users/varunreddy/Downloads/text2sql-framework-main/text2sql/agent.py) — Added Ollama provider
- [pyproject.toml](file:///Users/varunreddy/Downloads/text2sql-framework-main/pyproject.toml) — Added `langchain-ollama` dependency

Data layer:
- [setup_dropout_db.py](file:///Users/varunreddy/Downloads/text2sql-framework-main/examples/setup_dropout_db.py) — 6 tables, 30 students
- [dropout_scenarios.md](file:///Users/varunreddy/Downloads/text2sql-framework-main/examples/dropout_scenarios.md) — LLM guidance

---

## Screenshots

### Dashboard Overview
Shows stat cards, risk distribution chart, and critical/high risk students list.

![Dashboard View](file:///Users/varunreddy/.gemini/antigravity/brain/1808e297-337e-4e53-98b3-2aa453134f28/dashboard_view_1777408711833.png)

### Student Registry
Filterable table with search, risk level filter, and status filter. Click any row for full profile modal.

![Students Table](file:///Users/varunreddy/.gemini/antigravity/brain/1808e297-337e-4e53-98b3-2aa453134f28/students_table_view_1777408731623.png)

### AI Chat
NLP-to-SQL chatbot with suggested questions. Uses Qwen 3.5 to generate SQL and returns data tables.

![AI Chat](file:///Users/varunreddy/.gemini/antigravity/brain/1808e297-337e-4e53-98b3-2aa453134f28/ai_chat_view_1777408754743.png)

---

## How to Run

```bash
cd /Users/varunreddy/Downloads/text2sql-framework-main

# 1. Ensure Ollama is running
ollama run qwen3.5:4b

# 2. Setup database (if not already done)
python examples/setup_dropout_db.py

# 3. Launch the dashboard
python webapp/app.py
```

Then open **http://localhost:5000** in your browser.

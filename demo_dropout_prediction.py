#!/usr/bin/env python
"""
School Dropout Prediction — NLP to SQL Chatbot

Uses local Qwen 3.5:4b model via Ollama to translate natural language questions
about student dropout risk into SQL queries.

Prerequisites:
    1. Ollama running locally with qwen3.5:4b:
         ollama run qwen3.5:4b
    2. Install dependencies:
         pip install -e ".[ollama]"

Usage:
    python examples/demo_dropout_prediction.py
"""
import os
import sys

# ── 1. Create / refresh the dummy database ─────────────────────────────────

from sqlalchemy import create_engine, text

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dropout_prediction.db")

# Run the setup script if DB doesn't exist
if not os.path.exists(DB_PATH):
    print("📦 Setting up dropout prediction database...")
    setup_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "setup_dropout_db.py")
    exec(open(setup_script).read())
else:
    print(f"📦 Using existing database: {DB_PATH}")

# Quick sanity check
engine = create_engine(f"sqlite:///{DB_PATH}")
with engine.connect() as conn:
    count = conn.execute(text("SELECT COUNT(*) FROM students")).fetchone()[0]
    print(f"   → {count} students in database\n")

# ── 2. Initialize text2sql with local Ollama model ─────────────────────────

from text2sql import TextSQL

MODEL = "ollama:qwen3.5:4b"
SCENARIOS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dropout_scenarios.md")

print(f"🤖 Model: {MODEL} (local via Ollama)")
print(f"📋 Example scenarios: {SCENARIOS_PATH}\n")

tsql = TextSQL(
    f"sqlite:///{DB_PATH}",
    model=MODEL,
    instructions=(
        "This is a school dropout prediction database for Indian schools. "
        "Tables track students, parents, academics, socioeconomic conditions, "
        "school info, and risk assessments. Use these to answer questions about "
        "student dropout risk. Always explore the schema first."
    ),
    examples=SCENARIOS_PATH,
)

# ── 3. Run preset demo questions ───────────────────────────────────────────

demo_questions = [
    "Which students have a critical dropout risk level? Show their names, risk scores, and contributing factors.",
    "What is the average parent income for students at high or critical risk of dropping out?",
    "How many students live more than 15 km from school and have a parent with criminal history?",
]

print("=" * 70)
print("  DEMO: Preset Questions")
print("=" * 70)

for q in demo_questions:
    print(f"\n{'─' * 70}")
    print(f"❓ Q: {q}")
    print(f"{'─' * 70}")
    try:
        result = tsql.ask(q)
        print(f"📝 SQL: {result.sql}")
        print(f"   ({result.tool_calls_made} tool calls)")
        if result.error:
            print(f"❌ ERROR: {result.error}")
        elif result.data:
            for row in result.data[:10]:
                print(f"   → {row}")
        else:
            print("   (no rows returned)")
    except Exception as e:
        print(f"❌ Error: {e}")
    print()

# ── 4. Interactive REPL ────────────────────────────────────────────────────

print("\n" + "=" * 70)
print("  INTERACTIVE MODE — Type your questions in plain English")
print("  Type 'quit' or 'exit' to stop")
print("=" * 70 + "\n")

while True:
    try:
        question = input("🎓 You: ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\n👋 Bye!")
        break

    if not question:
        continue
    if question.lower() in ("quit", "exit", "q"):
        print("👋 Bye!")
        break

    try:
        result = tsql.ask(question)
        print(f"\n📝 SQL: {result.sql}")
        if result.error:
            print(f"❌ ERROR: {result.error}")
        elif result.data:
            for row in result.data[:15]:
                print(f"   → {row}")
            if len(result.data) > 15:
                print(f"   ... and {len(result.data) - 15} more rows")
        else:
            print("   (no rows returned)")
        if result.commentary:
            print(f"💬 {result.commentary}")
    except Exception as e:
        print(f"❌ Error: {e}")
    print()

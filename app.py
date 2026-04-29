#!/usr/bin/env python
"""
Flask backend for the School Dropout Prediction Dashboard.

Provides:
  - /                    → Serves the frontend
  - /api/chat            → NLP-to-SQL chatbot (POST)
  - /api/students        → All students with risk data (GET)
  - /api/stats           → Dashboard summary statistics (GET)
  - /api/query           → Direct SQL query for the dashboard (POST)

Usage:
    pip install flask
    python webapp/app.py
"""
import os
import sys
import sqlite3
import threading

from flask import Flask, request, jsonify, send_from_directory

# Add parent dir to path so we can import text2sql
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

app = Flask(__name__, static_folder="static")

# ── Database path ──────────────────────────────────────────────────────────
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "examples", "dropout_prediction.db")
DB_PATH = os.path.abspath(DB_PATH)

# ── Text2SQL engine (lazy-loaded, thread-safe) ────────────────────────────
_tsql = None
_tsql_lock = threading.Lock()

def get_tsql():
    global _tsql
    if _tsql is None:
        with _tsql_lock:
            if _tsql is None:
                from text2sql import TextSQL
                scenarios = os.path.join(
                    os.path.dirname(__file__), "..", "examples", "dropout_scenarios.md"
                )
                _tsql = TextSQL(
                    f"sqlite:///{DB_PATH}",
                    model="ollama:qwen3.5:4b",
                    instructions=(
                        "This is a school dropout prediction database for Indian schools. "
                        "Tables track students, parents, academics, socioeconomic conditions, "
                        "school info, and risk assessments. Use these to answer questions about "
                        "student dropout risk. Always explore the schema first."
                    ),
                    examples=scenarios,
                )
    return _tsql


def get_db():
    """Get a SQLite connection for direct queries."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ── API Routes ─────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/static/<path:path>")
def static_files(path):
    return send_from_directory("static", path)


@app.route("/api/chat", methods=["POST"])
def chat():
    """NLP-to-SQL chatbot endpoint."""
    data = request.get_json()
    question = data.get("question", "").strip()
    if not question:
        return jsonify({"error": "No question provided"}), 400

    try:
        tsql = get_tsql()
        result = tsql.ask(question)
        return jsonify({
            "question": question,
            "sql": result.sql,
            "data": result.data[:50],  # cap at 50 rows
            "error": result.error,
            "commentary": result.commentary,
            "tool_calls": result.tool_calls_made,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/students", methods=["GET"])
def students():
    """Get all students with risk data, parent info, and academics."""
    conn = get_db()
    try:
        rows = conn.execute("""
            SELECT
                s.student_id,
                s.first_name || ' ' || s.last_name AS name,
                s.gender,
                s.age,
                s.grade,
                s.current_status,
                s.distance_from_school_km,
                si.school_name,
                si.school_type,
                si.location AS school_location,
                p.annual_income AS parent_income,
                p.has_criminal_history,
                p.father_education,
                p.mother_education,
                a.gpa,
                a.attendance_pct,
                a.failed_subjects,
                a.behavior_grade,
                se.family_income_bracket,
                se.receives_scholarship,
                se.lives_with,
                se.number_of_siblings,
                se.has_internet_access,
                r.risk_score,
                r.risk_level,
                r.predicted_dropout_year,
                r.contributing_factors,
                r.recommended_intervention
            FROM students s
            JOIN school_info si ON s.school_id = si.school_id
            JOIN parents p ON s.parent_id = p.parent_id
            LEFT JOIN academics a ON s.student_id = a.student_id
            LEFT JOIN socioeconomic se ON s.student_id = se.student_id
            LEFT JOIN risk_assessments r ON s.student_id = r.student_id
            ORDER BY r.risk_score DESC
        """).fetchall()
        return jsonify([dict(row) for row in rows])
    finally:
        conn.close()


@app.route("/api/stats", methods=["GET"])
def stats():
    """Dashboard summary statistics."""
    conn = get_db()
    try:
        total = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        dropped = conn.execute("SELECT COUNT(*) FROM students WHERE current_status='dropped_out'").fetchone()[0]
        critical = conn.execute("SELECT COUNT(*) FROM risk_assessments WHERE risk_level='critical'").fetchone()[0]
        high = conn.execute("SELECT COUNT(*) FROM risk_assessments WHERE risk_level='high'").fetchone()[0]
        avg_gpa = conn.execute("SELECT ROUND(AVG(gpa), 2) FROM academics").fetchone()[0]
        avg_attendance = conn.execute("SELECT ROUND(AVG(attendance_pct), 1) FROM academics").fetchone()[0]
        avg_income = conn.execute("SELECT ROUND(AVG(annual_income), 0) FROM parents").fetchone()[0]

        # Risk distribution
        risk_dist = conn.execute("""
            SELECT risk_level, COUNT(*) as count
            FROM risk_assessments
            GROUP BY risk_level
            ORDER BY CASE risk_level
                WHEN 'critical' THEN 1
                WHEN 'high' THEN 2
                WHEN 'medium' THEN 3
                WHEN 'low' THEN 4
            END
        """).fetchall()

        # Status distribution
        status_dist = conn.execute("""
            SELECT current_status, COUNT(*) as count
            FROM students
            GROUP BY current_status
        """).fetchall()

        return jsonify({
            "total_students": total,
            "dropped_out": dropped,
            "critical_risk": critical,
            "high_risk": high,
            "avg_gpa": avg_gpa,
            "avg_attendance": avg_attendance,
            "avg_parent_income": avg_income,
            "risk_distribution": [dict(r) for r in risk_dist],
            "status_distribution": [dict(r) for r in status_dist],
        })
    finally:
        conn.close()


@app.route("/api/districts", methods=["GET"])
def districts():
    """Get per-district dropout aggregation."""
    conn = get_db()
    try:
        rows = conn.execute("""
            SELECT 
                si.location AS district,
                COUNT(s.student_id) AS total_students,
                SUM(CASE WHEN r.risk_level='High' THEN 1 ELSE 0 END) AS high_risk,
                SUM(CASE WHEN r.risk_level='Medium' THEN 1 ELSE 0 END) AS moderate_risk,
                SUM(CASE WHEN r.risk_level='Low' THEN 1 ELSE 0 END) AS low_risk,
                ROUND(AVG(a.attendance_pct), 1) AS avg_attendance,
                ROUND(AVG(a.gpa)*25, 1) AS avg_marks,
                ROUND(SUM(CASE WHEN s.current_status='dropped_out' THEN 1 ELSE 0 END)*100.0/COUNT(s.student_id), 1) AS dropout_rate,
                'stable' AS trend
            FROM students s
            JOIN school_info si ON s.school_id = si.school_id
            LEFT JOIN risk_assessments r ON s.student_id = r.student_id
            LEFT JOIN academics a ON s.student_id = a.student_id
            GROUP BY si.location
            ORDER BY high_risk DESC
        """).fetchall()
        return jsonify([dict(row) for row in rows])
    finally:
        conn.close()


@app.route("/api/monthly-trend", methods=["GET"])
def monthly_trend():
    """Mock monthly trend since we don't have time-series dates in the db yet."""
    return jsonify([
        {"month": "Jul", "total_dropouts": 2},
        {"month": "Aug", "total_dropouts": 5},
        {"month": "Sep", "total_dropouts": 8},
        {"month": "Oct", "total_dropouts": 12},
        {"month": "Nov", "total_dropouts": 15},
        {"month": "Dec", "total_dropouts": 20},
        {"month": "Jan", "total_dropouts": 25}
    ])


@app.route("/api/health", methods=["GET"])
def health():
    """Health check for backend connection."""
    conn = get_db()
    try:
        total = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        return jsonify({
            "status": "ok",
            "students_count": total,
            "monthly_records": 1250
        })
    finally:
        conn.close()


if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found at {DB_PATH}")
        print("   Run: python examples/setup_dropout_db.py")
        sys.exit(1)

    print(f"📦 Database: {DB_PATH}")
    print(f"🤖 Model: ollama:qwen3.5:4b")
    print(f"🌐 Starting server at http://localhost:5000")
    print(f"   Dashboard: http://localhost:5000")
    app.run(debug=True, port=5000)

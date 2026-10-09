import os
import psycopg2
from flask import Flask, jsonify, request, render_template
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
# Trust proxy headers from Nginx reverse proxy
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)

DATABASE_URL = os.getenv("DATABASE_URL")


def get_db_connection():
    return psycopg2.connect(DATABASE_URL)


def init_db():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL
        )
    """)

    conn.commit()
    cur.close()
    conn.close()


# init_db() is NOT called at module level so the module can be imported
# without a live database (e.g. during testing or linting).
# When the app is started directly (python app.py / Docker CMD), init_db()
# runs inside the __main__ block below.


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@app.route("/settings")
def settings():
    return render_template("settings.html")


@app.route("/health")
def health():
    """Health check that verifies the database is reachable."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        conn.close()
        return jsonify({
            "status": "healthy",
            "database": "connected"
        }), 200
    except Exception:
        return jsonify({
            "status": "unhealthy",
            "database": "unreachable"
        }), 503


@app.route("/tasks", methods=["GET"])
def get_tasks():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, title FROM tasks ORDER BY id")
    rows = cur.fetchall()

    cur.close()
    conn.close()

    tasks = [
        {"id": row[0], "title": row[1]}
        for row in rows
    ]

    return jsonify(tasks), 200


@app.route("/tasks", methods=["POST"])
def create_task():
    data = request.get_json()

    if not data or "title" not in data:
        return jsonify({
            "error": "Task title is required"
        }), 400

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO tasks (title) VALUES (%s) RETURNING id, title",
        (data["title"],)
    )

    row = cur.fetchone()

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({
        "id": row[0],
        "title": row[1]
    }), 201


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=8000)

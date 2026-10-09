import os
import datetime
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
            title TEXT NOT NULL,
            description TEXT,
            deadline DATE
        )
    """)

    # Safe idempotent migration for existing databases
    cur.execute("""
        ALTER TABLE tasks ADD COLUMN IF NOT EXISTS description TEXT;
        ALTER TABLE tasks ADD COLUMN IF NOT EXISTS deadline DATE;
    """)

    conn.commit()
    cur.close()
    conn.close()


def parse_deadline(val):
    if not val:
        return None
    val_str = str(val).strip()
    if not val_str:
        return None
    try:
        return datetime.date.fromisoformat(val_str)
    except ValueError:
        raise ValueError("Invalid deadline format. Expected YYYY-MM-DD.")


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


@app.route("/system-overview")
def system_overview():
    return render_template("system_overview.html")


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

    cur.execute(
        "SELECT id, title, description, deadline FROM tasks ORDER BY id"
    )
    rows = cur.fetchall()

    cur.close()
    conn.close()

    tasks = [
        {
            "id": row[0],
            "title": row[1],
            "description": row[2] if row[2] is not None else "",
            "deadline": row[3].isoformat() if row[3] is not None else None,
        }
        for row in rows
    ]

    return jsonify(tasks), 200


@app.route("/tasks", methods=["POST"])
def create_task():
    data = request.get_json()

    if not data or "title" not in data or not str(data["title"]).strip():
        return jsonify({
            "error": "Task title is required"
        }), 400

    title = str(data["title"]).strip()
    description = data.get("description")
    if description is not None:
        description = str(description).strip()
        if not description:
            description = None

    deadline_raw = data.get("deadline")
    try:
        deadline = parse_deadline(deadline_raw)
    except ValueError as e:
        return jsonify({
            "error": str(e)
        }), 400

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO tasks (title, description, deadline)
        VALUES (%s, %s, %s)
        RETURNING id, title, description, deadline
        """,
        (title, description, deadline)
    )

    row = cur.fetchone()

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({
        "id": row[0],
        "title": row[1],
        "description": row[2] if row[2] is not None else "",
        "deadline": row[3].isoformat() if row[3] is not None else None,
    }), 201


@app.route("/tasks/<int:task_id>", methods=["PUT"])
def update_task(task_id):
    data = request.get_json()

    if not data or "title" not in data or not str(data["title"]).strip():
        return jsonify({
            "error": "Task title is required"
        }), 400

    title = str(data["title"]).strip()
    description = data.get("description")
    if description is not None:
        description = str(description).strip()
        if not description:
            description = None

    deadline_raw = data.get("deadline")
    try:
        deadline = parse_deadline(deadline_raw)
    except ValueError as e:
        return jsonify({
            "error": str(e)
        }), 400

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE tasks
        SET title = %s, description = %s, deadline = %s
        WHERE id = %s
        RETURNING id, title, description, deadline
        """,
        (title, description, deadline, task_id)
    )
    row = cur.fetchone()

    conn.commit()
    cur.close()
    conn.close()

    if not row:
        return jsonify({"error": "Task not found"}), 404

    return jsonify({
        "id": row[0],
        "title": row[1],
        "description": row[2] if row[2] is not None else "",
        "deadline": row[3].isoformat() if row[3] is not None else None,
    }), 200


@app.route("/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM tasks WHERE id = %s RETURNING id",
        (task_id,)
    )
    row = cur.fetchone()

    conn.commit()
    cur.close()
    conn.close()

    if not row:
        return jsonify({"error": "Task not found"}), 404

    return jsonify({
        "message": "Task deleted successfully",
        "id": task_id
    }), 200


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=8000)

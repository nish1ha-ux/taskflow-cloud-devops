import os
import datetime
import psycopg2
from flask import Flask, jsonify, request, render_template
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
# Trust proxy headers from Nginx reverse proxy
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)

DATABASE_URL = os.getenv("DATABASE_URL")

DEFAULT_PROFILE = {
    "id": 1,
    "full_name": "TaskFlow User",
    "display_name": "User",
    "email": "",
    "avatar_color": "#6d8cff",
    "workspace_name": "Default Workspace",
    "workspace_description": "Production task and cloud DevOps workspace",
    "role": "Workspace Administrator",
    "timezone": "UTC (UTC+00:00)",
}


def compute_initials(full_name, display_name):
    name = (full_name or display_name or "TF").strip()
    parts = name.split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[1][0]).upper()
    elif len(parts) == 1 and len(parts[0]) >= 2:
        return parts[0][:2].upper()
    elif len(parts) == 1 and len(parts[0]) == 1:
        return parts[0][0].upper()
    return "TF"


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

    # Workspace & account profile table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS profile (
            id INT PRIMARY KEY,
            full_name TEXT NOT NULL,
            display_name TEXT NOT NULL,
            email TEXT,
            avatar_color TEXT,
            workspace_name TEXT NOT NULL,
            workspace_description TEXT,
            role TEXT,
            timezone TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("SELECT id FROM profile WHERE id = 1")
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO profile (
                id, full_name, display_name, email, avatar_color,
                workspace_name, workspace_description, role, timezone
            ) VALUES (
                1, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """, (
            DEFAULT_PROFILE["full_name"],
            DEFAULT_PROFILE["display_name"],
            DEFAULT_PROFILE["email"],
            DEFAULT_PROFILE["avatar_color"],
            DEFAULT_PROFILE["workspace_name"],
            DEFAULT_PROFILE["workspace_description"],
            DEFAULT_PROFILE["role"],
            DEFAULT_PROFILE["timezone"],
        ))

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


@app.route("/profile", methods=["GET"])
def get_profile():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, full_name, display_name, email, avatar_color,
               workspace_name, workspace_description, role, timezone
        FROM profile
        WHERE id = 1
    """)
    row = cur.fetchone()

    if not row:
        cur.execute("""
            INSERT INTO profile (
                id, full_name, display_name, email, avatar_color,
                workspace_name, workspace_description, role, timezone
            ) VALUES (
                1, %s, %s, %s, %s, %s, %s, %s, %s
            ) RETURNING id, full_name, display_name, email, avatar_color,
                        workspace_name, workspace_description, role, timezone
        """, (
            DEFAULT_PROFILE["full_name"],
            DEFAULT_PROFILE["display_name"],
            DEFAULT_PROFILE["email"],
            DEFAULT_PROFILE["avatar_color"],
            DEFAULT_PROFILE["workspace_name"],
            DEFAULT_PROFILE["workspace_description"],
            DEFAULT_PROFILE["role"],
            DEFAULT_PROFILE["timezone"],
        ))
        row = cur.fetchone()
        conn.commit()

    cur.close()
    conn.close()

    full_name = row[1]
    display_name = row[2]
    return jsonify({
        "id": row[0],
        "full_name": full_name,
        "display_name": display_name,
        "email": row[3] or "",
        "avatar_color": row[4] or "#6d8cff",
        "workspace_name": row[5],
        "workspace_description": row[6] or "",
        "role": row[7] or "",
        "timezone": row[8] or "",
        "initials": compute_initials(full_name, display_name),
    }), 200


@app.route("/profile", methods=["PUT", "POST"])
def update_profile():
    data = request.get_json(silent=True)
    if data is None or not isinstance(data, dict):
        return jsonify({
            "error": "Request body must be valid JSON object"
        }), 400

    full_name = str(data.get("full_name") or "").strip()
    display_name = str(data.get("display_name") or "").strip()
    workspace_name = str(data.get("workspace_name") or "").strip()

    if not full_name:
        return jsonify({"error": "Full name is required"}), 400
    if not display_name:
        return jsonify({"error": "Display name is required"}), 400
    if not workspace_name:
        return jsonify({"error": "Workspace name is required"}), 400

    email = data.get("email")
    email = str(email).strip() if email is not None else ""

    avatar_color = data.get("avatar_color")
    avatar_color = str(avatar_color).strip() if avatar_color else "#6d8cff"

    workspace_description = data.get("workspace_description")
    workspace_description = (
        str(workspace_description).strip()
        if workspace_description is not None else ""
    )

    role = data.get("role")
    role = str(role).strip() if role is not None else ""

    timezone = data.get("timezone")
    timezone = str(timezone).strip() if timezone is not None else ""

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO profile (
            id, full_name, display_name, email, avatar_color,
            workspace_name, workspace_description, role, timezone,
            updated_at
        ) VALUES (
            1, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP
        )
        ON CONFLICT (id) DO UPDATE SET
            full_name = EXCLUDED.full_name,
            display_name = EXCLUDED.display_name,
            email = EXCLUDED.email,
            avatar_color = EXCLUDED.avatar_color,
            workspace_name = EXCLUDED.workspace_name,
            workspace_description = EXCLUDED.workspace_description,
            role = EXCLUDED.role,
            timezone = EXCLUDED.timezone,
            updated_at = CURRENT_TIMESTAMP
        RETURNING id, full_name, display_name, email, avatar_color,
                  workspace_name, workspace_description, role, timezone
    """, (
        full_name,
        display_name,
        email,
        avatar_color,
        workspace_name,
        workspace_description,
        role,
        timezone,
    ))
    row = cur.fetchone()

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({
        "id": row[0],
        "full_name": row[1],
        "display_name": row[2],
        "email": row[3] or "",
        "avatar_color": row[4] or "#6d8cff",
        "workspace_name": row[5],
        "workspace_description": row[6] or "",
        "role": row[7] or "",
        "timezone": row[8] or "",
        "initials": compute_initials(row[1], row[2]),
        "message": "Profile updated successfully",
    }), 200


@app.route("/profile/reset", methods=["POST"])
def reset_profile():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO profile (
            id, full_name, display_name, email, avatar_color,
            workspace_name, workspace_description, role, timezone,
            updated_at
        ) VALUES (
            1, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP
        )
        ON CONFLICT (id) DO UPDATE SET
            full_name = EXCLUDED.full_name,
            display_name = EXCLUDED.display_name,
            email = EXCLUDED.email,
            avatar_color = EXCLUDED.avatar_color,
            workspace_name = EXCLUDED.workspace_name,
            workspace_description = EXCLUDED.workspace_description,
            role = EXCLUDED.role,
            timezone = EXCLUDED.timezone,
            updated_at = CURRENT_TIMESTAMP
        RETURNING id, full_name, display_name, email, avatar_color,
                  workspace_name, workspace_description, role, timezone
    """, (
        DEFAULT_PROFILE["full_name"],
        DEFAULT_PROFILE["display_name"],
        DEFAULT_PROFILE["email"],
        DEFAULT_PROFILE["avatar_color"],
        DEFAULT_PROFILE["workspace_name"],
        DEFAULT_PROFILE["workspace_description"],
        DEFAULT_PROFILE["role"],
        DEFAULT_PROFILE["timezone"],
    ))
    row = cur.fetchone()

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({
        "id": row[0],
        "full_name": row[1],
        "display_name": row[2],
        "email": row[3] or "",
        "avatar_color": row[4] or "#6d8cff",
        "workspace_name": row[5],
        "workspace_description": row[6] or "",
        "role": row[7] or "",
        "timezone": row[8] or "",
        "initials": compute_initials(row[1], row[2]),
        "message": "Profile reset to default successfully",
    }), 200


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=8000)

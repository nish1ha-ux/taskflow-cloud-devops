import pytest
from unittest.mock import patch, MagicMock

from app.app import app as flask_app


@pytest.fixture
def client():
    """Create a Flask test client."""
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


# ── Health endpoint ──────────────────────────────────────────────


def test_health_db_connected(client):
    """GET /health returns 200 when the database is reachable."""
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value = mock_cur

    with patch("app.app.get_db_connection", return_value=mock_conn):
        response = client.get("/health")

    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    mock_cur.execute.assert_called_once_with("SELECT 1")
    mock_cur.close.assert_called_once()
    mock_conn.close.assert_called_once()


def test_health_db_unreachable(client):
    """GET /health returns 503 when the database is unreachable."""
    err = Exception("conn refused")
    with patch("app.app.get_db_connection", side_effect=err):
        response = client.get("/health")

    assert response.status_code == 503

    data = response.get_json()
    assert data["status"] == "unhealthy"
    assert data["database"] == "unreachable"


# ── Home & Dashboard pages ───────────────────────────────────────


def test_home_returns_200(client):
    """GET / renders the index template with theme toggle and returns 200."""
    response = client.get("/")
    assert response.status_code == 200
    assert b'id="themeToggle"' in response.data
    assert b'id="notificationBtn"' in response.data
    assert b'id="settingsModal"' in response.data
    assert b"taskflow-theme" in response.data


def test_dashboard_returns_200(client):
    """GET /dashboard renders the dashboard template and returns 200."""
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert b"Welcome to Dashboard" in response.data
    assert b"Total Tasks" in response.data
    assert b'id="themeToggle"' in response.data
    assert b'id="notificationBtn"' in response.data
    assert b'id="settingsModal"' in response.data
    assert b"taskflow-theme" in response.data


def test_settings_returns_200(client):
    """GET /settings renders the settings template and returns 200."""
    response = client.get("/settings")
    assert response.status_code == 200
    assert b"Settings" in response.data
    assert b'id="appearanceSection"' in response.data
    assert b'id="accountSection"' in response.data
    assert b'id="notificationsSection"' in response.data
    assert b'id="appPreferencesSection"' in response.data
    assert b'id="themeToggle"' in response.data
    assert b'id="notificationBtn"' in response.data
    assert b'href="/system-overview"' in response.data
    assert b"taskflow-theme" in response.data
    assert b"taskflow-workspace-name" in response.data


def test_system_overview_returns_200(client):
    """GET /system-overview renders template and returns 200."""
    response = client.get("/system-overview")
    assert response.status_code == 200
    assert b"About TaskFlow Cloud DevOps" in response.data
    assert b"Platform Specifications" in response.data
    assert b"Deployment Topology" in response.data
    assert b'id="aboutSection"' in response.data
    assert b'id="themeToggle"' in response.data
    assert b'id="notificationBtn"' in response.data
    assert b'id="refreshHealthBtn"' in response.data
    assert b"taskflow-theme" in response.data
    assert b"taskflow-workspace-name" in response.data


# ── Task creation validation ────────────────────────────────────


def test_create_task_missing_title(client):
    """POST /tasks with empty JSON body returns 400."""
    response = client.post("/tasks", json={})
    assert response.status_code == 400
    data = response.get_json()
    assert data["error"] == "Task title is required"


def test_create_task_no_body(client):
    """POST /tasks with no JSON body at all returns 400.

    Flask rejects the malformed JSON before the route handler runs,
    so the response is an HTML 400 — we only assert the status code.
    """
    response = client.post(
        "/tasks",
        data="",
        content_type="application/json",
    )
    assert response.status_code == 400


def test_create_task_null_title(client):
    """POST /tasks with title explicitly set to null returns 400."""
    response = client.post("/tasks", json={"not_title": "ignored"})
    assert response.status_code == 400
    data = response.get_json()
    assert data["error"] == "Task title is required"


# ── Tasks retrieval and creation ─────────────────────────────────


def test_get_tasks_success(client):
    """GET /tasks returns 200 with list of tasks."""
    import datetime
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value = mock_cur
    mock_cur.fetchall.return_value = [
        (1, "First task", "A sample description", datetime.date(2026, 10, 15)),
        (2, "Second task", None, None),
    ]

    with patch("app.app.get_db_connection", return_value=mock_conn):
        response = client.get("/tasks")

    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 2
    assert data[0] == {
        "id": 1,
        "title": "First task",
        "description": "A sample description",
        "deadline": "2026-10-15",
    }
    assert data[1] == {
        "id": 2,
        "title": "Second task",
        "description": "",
        "deadline": None,
    }
    mock_cur.execute.assert_called_once_with(
        "SELECT id, title, description, deadline FROM tasks ORDER BY id"
    )
    mock_cur.close.assert_called_once()
    mock_conn.close.assert_called_once()


def test_create_task_title_only(client):
    """POST /tasks with only title creates a task and returns 201."""
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value = mock_cur
    mock_cur.fetchone.return_value = (10, "New Test Task", None, None)

    with patch("app.app.get_db_connection", return_value=mock_conn):
        response = client.post("/tasks", json={"title": "New Test Task"})

    assert response.status_code == 201
    data = response.get_json()
    assert data == {
        "id": 10,
        "title": "New Test Task",
        "description": "",
        "deadline": None,
    }
    mock_conn.commit.assert_called_once()
    mock_cur.close.assert_called_once()
    mock_conn.close.assert_called_once()


def test_create_task_with_desc_and_deadline(client):
    """POST /tasks with description and deadline creates task."""
    import datetime
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value = mock_cur
    mock_cur.fetchone.return_value = (
        11,
        "Complete Project",
        "Detailed step by step plan",
        datetime.date(2026, 12, 31),
    )

    with patch("app.app.get_db_connection", return_value=mock_conn):
        response = client.post("/tasks", json={
            "title": "Complete Project",
            "description": "Detailed step by step plan",
            "deadline": "2026-12-31",
        })

    assert response.status_code == 201
    data = response.get_json()
    assert data == {
        "id": 11,
        "title": "Complete Project",
        "description": "Detailed step by step plan",
        "deadline": "2026-12-31",
    }
    mock_conn.commit.assert_called_once()
    mock_cur.close.assert_called_once()
    mock_conn.close.assert_called_once()


def test_create_task_invalid_deadline(client):
    """POST /tasks with invalid deadline string returns 400."""
    response = client.post("/tasks", json={
        "title": "Invalid Date Task",
        "deadline": "not-a-valid-date",
    })
    assert response.status_code == 400
    data = response.get_json()
    assert "Invalid deadline format" in data["error"]


def test_update_task_success(client):
    """PUT /tasks/<id> updates task and returns 200."""
    import datetime
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value = mock_cur
    mock_cur.fetchone.return_value = (
        5,
        "Updated Task Title",
        "Updated Description",
        datetime.date(2026, 11, 20),
    )

    with patch("app.app.get_db_connection", return_value=mock_conn):
        response = client.put("/tasks/5", json={
            "title": "Updated Task Title",
            "description": "Updated Description",
            "deadline": "2026-11-20",
        })

    assert response.status_code == 200
    data = response.get_json()
    assert data == {
        "id": 5,
        "title": "Updated Task Title",
        "description": "Updated Description",
        "deadline": "2026-11-20",
    }
    mock_conn.commit.assert_called_once()
    mock_cur.close.assert_called_once()
    mock_conn.close.assert_called_once()


def test_update_task_clear_optional_fields(client):
    """PUT /tasks/<id> clearing description and deadline returns 200."""
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value = mock_cur
    mock_cur.fetchone.return_value = (5, "Cleaned Task", None, None)

    with patch("app.app.get_db_connection", return_value=mock_conn):
        response = client.put("/tasks/5", json={
            "title": "Cleaned Task",
            "description": "",
            "deadline": None,
        })

    assert response.status_code == 200
    data = response.get_json()
    assert data == {
        "id": 5,
        "title": "Cleaned Task",
        "description": "",
        "deadline": None,
    }


def test_update_task_invalid_deadline(client):
    """PUT /tasks/<id> with invalid deadline returns 400."""
    response = client.put("/tasks/5", json={
        "title": "Valid Title",
        "deadline": "invalid-deadline",
    })
    assert response.status_code == 400
    data = response.get_json()
    assert "Invalid deadline format" in data["error"]


def test_update_task_not_found(client):
    """PUT /tasks/<id> returns 404 if task does not exist."""
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value = mock_cur
    mock_cur.fetchone.return_value = None

    with patch("app.app.get_db_connection", return_value=mock_conn):
        response = client.put("/tasks/999", json={"title": "Nonexistent"})

    assert response.status_code == 404
    data = response.get_json()
    assert data["error"] == "Task not found"


def test_update_task_missing_title(client):
    """PUT /tasks/<id> returns 400 if title is empty or missing."""
    response = client.put("/tasks/5", json={"title": "   "})
    assert response.status_code == 400
    data = response.get_json()
    assert data["error"] == "Task title is required"


def test_delete_task_success(client):
    """DELETE /tasks/<id> deletes the task and returns 200."""
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value = mock_cur
    mock_cur.fetchone.return_value = (5,)

    with patch("app.app.get_db_connection", return_value=mock_conn):
        response = client.delete("/tasks/5")

    assert response.status_code == 200
    data = response.get_json()
    assert data["message"] == "Task deleted successfully"
    assert data["id"] == 5
    mock_conn.commit.assert_called_once()
    mock_cur.close.assert_called_once()
    mock_conn.close.assert_called_once()


def test_delete_task_not_found(client):
    """DELETE /tasks/<id> returns 404 if task does not exist."""
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value = mock_cur
    mock_cur.fetchone.return_value = None

    with patch("app.app.get_db_connection", return_value=mock_conn):
        response = client.delete("/tasks/999")

    assert response.status_code == 404
    data = response.get_json()
    assert data["error"] == "Task not found"


def test_init_db():
    """init_db creates tasks table and migrates columns if needed."""
    from app.app import init_db

    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value = mock_cur

    with patch("app.app.get_db_connection", return_value=mock_conn):
        init_db()

    assert mock_cur.execute.call_count == 2
    create_call = mock_cur.execute.call_args_list[0][0][0]
    alter_call = mock_cur.execute.call_args_list[1][0][0]
    assert "CREATE TABLE IF NOT EXISTS tasks" in create_call
    assert "ALTER TABLE tasks ADD COLUMN IF NOT EXISTS description" in (
        alter_call
    )
    assert "ALTER TABLE tasks ADD COLUMN IF NOT EXISTS deadline" in (
        alter_call
    )
    mock_conn.commit.assert_called_once()
    mock_cur.close.assert_called_once()
    mock_conn.close.assert_called_once()

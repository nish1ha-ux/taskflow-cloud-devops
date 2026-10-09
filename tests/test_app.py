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
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value = mock_cur
    mock_cur.fetchall.return_value = [(1, "First task"), (2, "Second task")]

    with patch("app.app.get_db_connection", return_value=mock_conn):
        response = client.get("/tasks")

    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 2
    assert data[0] == {"id": 1, "title": "First task"}
    assert data[1] == {"id": 2, "title": "Second task"}
    mock_cur.execute.assert_called_once_with(
        "SELECT id, title FROM tasks ORDER BY id"
    )
    mock_cur.close.assert_called_once()
    mock_conn.close.assert_called_once()


def test_create_task_success(client):
    """POST /tasks with valid title creates a task and returns 201."""
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value = mock_cur
    mock_cur.fetchone.return_value = (10, "New Test Task")

    with patch("app.app.get_db_connection", return_value=mock_conn):
        response = client.post("/tasks", json={"title": "New Test Task"})

    assert response.status_code == 201
    data = response.get_json()
    assert data == {"id": 10, "title": "New Test Task"}
    mock_conn.commit.assert_called_once()
    mock_cur.close.assert_called_once()
    mock_conn.close.assert_called_once()


def test_init_db():
    """init_db creates tasks table if it does not exist."""
    from app.app import init_db

    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value = mock_cur

    with patch("app.app.get_db_connection", return_value=mock_conn):
        init_db()

    mock_cur.execute.assert_called_once()
    query = mock_cur.execute.call_args[0][0]
    assert "CREATE TABLE IF NOT EXISTS tasks" in query
    mock_conn.commit.assert_called_once()
    mock_cur.close.assert_called_once()
    mock_conn.close.assert_called_once()

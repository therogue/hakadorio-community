"""
Tests for FastAPI endpoints in main.py.
Does not test /chat endpoint (requires mocking Claude API).
Uses create_task_db to set up test data since POST /tasks was removed.
"""
from sqlmodel import Session

from database import create_task_db
import database
from models import Task


class TestTaskEndpoints:
    """Tests for /tasks endpoints."""

    def test_get_tasks_empty(self, app_client):
        """GET /tasks returns empty list when no tasks."""
        response = app_client.get("/tasks")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_tasks_returns_tasks(self, test_db, app_client):
        """GET /tasks returns created tasks."""
        create_task_db("id-1", "Task 1", "T")
        create_task_db("id-2", "Task 2", "T")

        response = app_client.get("/tasks")
        assert response.status_code == 200
        tasks = response.json()
        assert len(tasks) == 2

    def test_update_task_title(self, test_db, app_client):
        """PATCH /tasks/{id} updates title."""
        create_task_db("id-1", "Old title", "T")

        response = app_client.patch("/tasks/id-1", json={
            "title": "New title"
        })
        assert response.status_code == 200
        assert response.json()["title"] == "New title"

    def test_update_task_completed(self, test_db, app_client):
        """PATCH /tasks/{id} marks task completed."""
        create_task_db("id-1", "Complete me", "T")

        response = app_client.patch("/tasks/id-1", json={
            "completed": True
        })
        assert response.status_code == 200
        assert response.json()["completed"] is True

    def test_update_task_not_found(self, app_client):
        """PATCH /tasks/{id} returns 404 for nonexistent task."""
        response = app_client.patch("/tasks/nonexistent", json={
            "title": "New title"
        })
        assert response.status_code == 404

    def test_delete_task(self, test_db, app_client):
        """DELETE /tasks/{id} removes task."""
        create_task_db("id-1", "Delete me", "T")

        response = app_client.delete("/tasks/id-1")
        assert response.status_code == 200
        assert response.json()["status"] == "deleted"

        # Verify task is gone
        tasks = app_client.get("/tasks").json()
        assert len(tasks) == 0

    def test_delete_task_not_found(self, app_client):
        """DELETE /tasks/{id} returns 404 for nonexistent task."""
        response = app_client.delete("/tasks/nonexistent")
        assert response.status_code == 404


class TestOverdueEndpoint:
    """Tests for GET /tasks/overdue. Pins 'today' via monkeypatching main.datetime."""

    def _pin_today(self, monkeypatch, today_str: str):
        """Replace main.datetime so datetime.now() returns a fixed date."""
        import main
        from datetime import datetime as real_datetime

        class _FrozenDatetime(real_datetime):
            @classmethod
            def now(cls, tz=None):
                y, m, d = map(int, today_str.split("-"))
                return real_datetime(y, m, d)

        monkeypatch.setattr(main, "datetime", _FrozenDatetime)

    def test_returns_overdue_tasks(self, test_db, app_client, monkeypatch):
        self._pin_today(monkeypatch, "2025-06-15")
        create_task_db("old-1", "Old task", "T", "2025-06-01")
        create_task_db("today-1", "Today task", "T", "2025-06-15")
        create_task_db("future-1", "Future task", "T", "2025-06-20")

        response = app_client.get("/tasks/overdue")

        assert response.status_code == 200
        ids = [t["id"] for t in response.json()]
        assert ids == ["old-1"]

    def test_excludes_meetings_and_recurrent_instances(self, test_db, app_client, monkeypatch):
        self._pin_today(monkeypatch, "2025-06-15")
        create_task_db("mtg-1", "Old meeting", "M", "2025-06-01T09:00")
        create_task_db("tpl-1", "Stretch", "D", "2025-06-01", "daily", is_template=True)
        create_task_db("inst-1", "Stretch", "D", "2025-06-01", "daily",
                       is_template=False, parent_task_id="tpl-1")

        response = app_client.get("/tasks/overdue")

        assert response.status_code == 200
        assert response.json() == []


class TestConversationEndpoint:
    """Tests for /conversation endpoint."""

    def test_get_conversation_empty(self, app_client):
        """GET /conversation returns id=None and empty messages when no conversation exists."""
        response = app_client.get("/conversation")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] is None
        assert data["messages"] == []


class TestDaySummaryEndpoint:
    """Tests for POST /day-summary. LLM is mocked; today is pinned via main.datetime.

    Iteration 1: existence + happy-path only. Edges (idempotent return on second call,
    rename regeneration, empty day) deferred to iteration 2.
    """

    def _pin_today(self, monkeypatch, today_str: str):
        import main
        from datetime import datetime as real_datetime

        class _FrozenDatetime(real_datetime):
            @classmethod
            def now(cls, tz=None):
                y, m, d = map(int, today_str.split("-"))
                return real_datetime(y, m, d)

        monkeypatch.setattr(main, "datetime", _FrozenDatetime)

    def _mock_summary(self, monkeypatch, text: str):
        """Replace generate_day_summary with an async stub that returns `text`."""
        import main

        async def _stub(today: str) -> str:
            return text

        monkeypatch.setattr(main, "generate_day_summary", _stub)

    def test_first_call_creates_conversation_with_date_title(self, test_db, app_client, monkeypatch):
        self._pin_today(monkeypatch, "2026-05-02")
        self._mock_summary(monkeypatch, "Light day. Just one meeting.")

        response = app_client.post("/day-summary")

        assert response.status_code == 200
        data = response.json()
        assert data["created"] is True
        assert data["summary"] == "Light day. Just one meeting."
        assert isinstance(data["conversation_id"], int)

        # Conversation persisted with title = today and summary as first assistant message
        conv_resp = app_client.get(f"/conversations/{data['conversation_id']}")
        assert conv_resp.status_code == 200
        conv = conv_resp.json()
        assert len(conv["messages"]) == 1
        assert conv["messages"][0]["role"] == "assistant"
        assert conv["messages"][0]["content"] == "Light day. Just one meeting."

        # Title contains today's date
        list_resp = app_client.get("/conversations")
        titles = [c["title"] for c in list_resp.json() if c["id"] == data["conversation_id"]]
        assert any("2026-05-02" in t for t in titles)

    def test_second_call_returns_existing_no_duplicate(self, test_db, app_client, monkeypatch):
        """When a conversation whose title contains today already exists, second POST returns
        that conversation's id and its first assistant message with created=false. No duplicate.
        """
        self._pin_today(monkeypatch, "2026-05-02")
        self._mock_summary(monkeypatch, "First summary.")

        first = app_client.post("/day-summary").json()
        assert first["created"] is True
        first_id = first["conversation_id"]

        # Mock returns a different summary; endpoint must NOT call the LLM again / use the new text
        self._mock_summary(monkeypatch, "Should-not-be-used regeneration.")
        second = app_client.post("/day-summary").json()

        assert second["created"] is False
        assert second["conversation_id"] == first_id
        assert second["summary"] == "First summary."

        # Exactly one conversation matching today's date
        list_resp = app_client.get("/conversations").json()
        matching = [c for c in list_resp if "2026-05-02" in (c.get("title") or "")]
        assert len(matching) == 1

    def test_empty_day_returns_non_empty_summary(self, test_db, app_client, monkeypatch):
        """Characterization (AC5): with no scheduled tasks, endpoint still returns 200 with a
        non-empty summary string. Guards against an impl that short-circuits on empty days.
        """
        self._pin_today(monkeypatch, "2026-05-02")
        self._mock_summary(monkeypatch, "Nothing planned today, enjoy the calm.")

        response = app_client.post("/day-summary")
        assert response.status_code == 200
        data = response.json()
        assert data["summary"] == "Nothing planned today, enjoy the calm."
        assert data["created"] is True

    def test_rename_regenerates_new_conversation(self, test_db, app_client, monkeypatch):
        """Characterization (AC7): if a previously-titled YYYY-MM-DD conversation is renamed
        to omit the date, next /day-summary creates a new conversation with created=true.
        Guards AC2 idempotency from over-matching arbitrary recent conversations.
        """
        self._pin_today(monkeypatch, "2026-05-02")
        self._mock_summary(monkeypatch, "Original.")

        first = app_client.post("/day-summary").json()
        first_id = first["conversation_id"]

        rename_resp = app_client.patch(f"/conversations/{first_id}/title", json={"title": "Random title"})
        assert rename_resp.status_code == 200

        self._mock_summary(monkeypatch, "Regenerated.")
        second = app_client.post("/day-summary").json()

        assert second["created"] is True
        assert second["conversation_id"] != first_id
        assert second["summary"] == "Regenerated."


class TestTemplateInstanceBehavior:
    """Test template and instance behavior through API."""

    def test_instance_completes_normally(self, test_db, app_client):
        """Instances (non-templates) complete normally without date advancement."""
        create_task_db("id-1", "Daily task instance", "D", "2025-01-20", "daily", is_template=False)

        response = app_client.patch("/tasks/id-1", json={
            "completed": True
        })

        assert response.status_code == 200
        data = response.json()
        assert data["completed"] is True
        assert data["scheduled_date"] == "2025-01-20"

    def test_template_created_with_r_prefix(self, test_db, app_client):
        """Templates have R- prefix in task_key."""
        task = create_task_db("id-1", "Daily standup", "D", "2025-01-20", "daily", is_template=True)

        assert task.is_template is True
        assert task.task_key.startswith("R-")
        assert task.task_key == "R-D-01"

    def test_get_tasks_for_date_creates_instance(self, test_db, app_client):
        """Day view for today creates instance from matching template."""
        # Insert template via ORM with specific created_at
        with Session(database.engine) as session:
            session.add(Task(
                id="tpl-1",
                task_key="R-D-01",
                category="D",
                task_number=1,
                title="Daily standup",
                completed=False,
                scheduled_date="2025-01-20",
                recurrence_rule="daily",
                created_at="2025-01-20T10:00:00",
                is_template=True,
                parent_task_id=None,
            ))
            session.commit()

        # Get tasks for 2025-01-21 (pattern matches, after created_at)
        response = app_client.get("/tasks/for-date?date=2025-01-21")
        assert response.status_code == 200
        tasks = response.json()

        assert len(tasks) == 1
        assert tasks[0]["title"] == "Daily standup"


class TestSettingsEndpoints:
    """Tests for GET /settings and PATCH /settings."""

    def test_get_settings_returns_defaults(self, app_client):
        """GET /settings returns default values."""
        response = app_client.get("/settings")
        assert response.status_code == 200
        data = response.json()
        assert data["default_category"] == "T"
        assert data["default_priority"] == "medium"
        assert data["conflict_resolution"] == "overlap"

    def test_patch_settings_updates_all_fields(self, app_client):
        """PATCH /settings updates all fields."""
        response = app_client.patch("/settings", json={
            "default_category": "M",
            "default_priority": "high",
            "conflict_resolution": "backlog",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["default_category"] == "M"
        assert data["default_priority"] == "high"
        assert data["conflict_resolution"] == "backlog"

    def test_patch_settings_partial_update(self, app_client):
        """PATCH /settings partial payload only changes specified fields."""
        app_client.patch("/settings", json={
            "default_category": "D",
            "default_priority": "low",
            "conflict_resolution": "unschedule",
        })
        response = app_client.patch("/settings", json={"default_priority": "critical"})
        assert response.status_code == 200
        data = response.json()
        assert data["default_category"] == "D"          # unchanged
        assert data["default_priority"] == "critical"   # updated
        assert data["conflict_resolution"] == "unschedule"  # unchanged

    def test_patch_settings_persists_across_calls(self, app_client):
        """Changes are visible in subsequent GET /settings."""
        app_client.patch("/settings", json={"default_priority": "none"})
        response = app_client.get("/settings")
        assert response.status_code == 200
        assert response.json()["default_priority"] == "none"

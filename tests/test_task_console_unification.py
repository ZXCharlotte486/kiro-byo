"""One-page task console and Crew-source-of-truth regression contracts."""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

from kiro_byo.crew_linkage import background_execution_snapshot
from test_crew_linkage import live_linkage_routes

ROOT = Path(__file__).resolve().parents[1]


def _body(response):
    return response.status, json.loads(response.text)


def test_background_execution_never_confuses_a_route_with_success():
    rows = [
        {"selection_source": "background_auto", "outcome": "error", "error_kind": "AttributeError", "error_site": "worker.py:77:run",
         "timestamp": 123, "provider_id": "xiaomi", "served_model": "mimo-v2.6-flash", "input_tokens": 0,
         "output_tokens": 0, "total_ms": 21500},
        {"selection_source": "user_set_config", "outcome": "success", "served_model": "foreign"},
    ]
    report = background_execution_snapshot(rows)
    assert report["failed_recent"] == 1
    row = report["latest"]
    assert row["recorded_by"] == "kiro-byo"
    assert row["error_kind"] == "AttributeError"
    assert row["error_site"] == "worker.py:77:run"
    assert row["served_model"] == "mimo-v2.6-flash"
    assert row["upstream_verified"] is False
    assert len(report["recent"]) == 1
    assert background_execution_snapshot([])["latest"] is None


def test_task_console_ui_does_not_duplicate_chat_or_member_picker():
    js = (ROOT / "ui/index.mjs").read_text(encoding="utf-8")
    chunk = js.split("function TasksPage(", 1)[1].split("function RecordsPage(", 1)[0]
    assert "chatCard" not in chunk
    assert "membersCard" not in chunk
    assert "previewSwitch" not in chunk
    assert "task_console.background" in chunk
    assert "task_console.schedules" in chunk
    assert "task_console.recent" in chunk
    assert "expected_model:t.model" in chunk
    assert "expected_model:background.model" in chunk
    assert "onNavigate?.('records')" in chunk
    assert "12000" in chunk


def test_stale_background_selection_cannot_overwrite_native_crew(live_linkage_routes):
    host = live_linkage_routes
    code, body = _body(asyncio.run(host.routes.update_background_model(
        host.request({"model": "byo-model", "expected_model": "different"}), None
    )))
    assert code == 400
    assert "changed" in body["error"]
    assert host.document["agent"]["role_models"]["background"] == "auto"
    code, body = _body(asyncio.run(host.routes.update_background_model(
        host.request({"model": "byo-model", "expected_model": "auto"}), None
    )))
    assert code == 200, body
    assert host.document["agent"]["role_models"]["background"] == "byo-model"
    assert body["background"]["verified"] is True


def test_stale_schedule_selection_cannot_overwrite_crew(live_linkage_routes):
    from types import SimpleNamespace
    host = live_linkage_routes
    request = host.request({"model": "byo-model", "expected_model": "old"})
    async def jobs(**kwargs):
        return [SimpleNamespace(id="example", model="new", script="", command="")]
    request.app["state"].crons.list_jobs_async = jobs
    code, body = _body(asyncio.run(host.routes.update_task_model(request, None)))
    assert code == 400
    assert "changed" in body["error"]


def test_official_mode_guards_context_and_auto_model(live_linkage_routes):
    host = live_linkage_routes
    host.document["agent"]["acp_backend"] = "kas"
    for method, payload in (
        (host.routes.update_background_model, {"model": "auto"}),
        (host.routes.update_task_model, {"model": ""}),
        (host.routes.update_task_execution, {"persistent_session": True, "minimal_context": False}),
    ):
        code, _ = _body(asyncio.run(method(host.request(payload), None)))
        assert code == 400


def test_telemetry_only_reports_byo_background_auto(live_linkage_routes, monkeypatch):
    host = live_linkage_routes
    class Store:
        def recent(self, limit):
            assert limit == 30
            return [
                {"selection_source": "user_set_config", "outcome": "success", "served_model": "chat"},
                {"selection_source": "background_auto", "outcome": "error", "error_kind": "AttributeError",
                 "provider_id": "xiaomi", "served_model": "mimo-v2.6-flash"},
            ]
    monkeypatch.setattr(host.routes, "TurnTelemetryStore", Store)
    code, payload = _body(asyncio.run(host.routes.get_tasks(host.request(), None)))
    assert code == 200, payload
    assert payload["background"]["model"] == "auto"
    assert payload["execution"]["latest"]["error_kind"] == "AttributeError"
    assert len(payload["execution"]["recent"]) == 1
    assert payload["config_source"] == "kirocrew_native"
    assert payload["main_backend"] == "kiro-byo"


def test_explicit_background_role_is_tracked_with_pinned_concrete_model():
    rows = [{"is_background_role": True, "selection_source": "host_session_new",
             "outcome": "success", "served_model": "pinned", "provider_id": "custom"},
            {"is_background_role": False, "selection_source": "user_set_config",
             "outcome": "success", "served_model": "chat"}]
    report = background_execution_snapshot(rows)
    assert len(report["recent"]) == 1
    assert report["latest"]["served_model"] == "pinned"
    assert report["latest"]["upstream_verified"] is True

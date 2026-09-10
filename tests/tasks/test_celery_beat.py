"""Beat jadvali va Celery routing nomlari testlari."""

from __future__ import annotations

import importlib

import pytest


@pytest.fixture(scope="module")
def celery_app():
    """Celery app instansiyasi."""
    from config.celery import app

    return app


def test_beat_schedule_tasks_are_importable(celery_app):
    """Beat jadvalidagi har bir task yo'li haqiqatan import qilinishi shart."""
    for name, entry in celery_app.conf.beat_schedule.items():
        task_path = entry["task"]
        module_path, _, attr = task_path.rpartition(".")
        module = importlib.import_module(module_path)
        assert getattr(module, attr, None) is not None, f"{name}: {task_path} topilmadi"


def test_beat_schedule_entries_match_expected_tasks(celery_app):
    """Beat jadvalidagi barcha 13.x task nomlari aniq bo'lishi shart."""
    expected = {
        "daily_usage_rollup": "apps.usage.tasks.daily_usage_rollup",
        "archive_old_conversations": "apps.chat.tasks.archive_old_conversations",
        "check_limits_and_notify": "apps.usage.tasks.check_limits_and_notify",
        "stock_low_alert": "apps.catalog.tasks.stock_low_alert",
    }
    schedule = celery_app.conf.beat_schedule
    assert expected.keys() <= schedule.keys()
    for name, task_path in expected.items():
        assert schedule[name]["task"] == task_path


def test_compress_image_task_route_matches_name(celery_app):
    """`compress_image` → `compress_image_task` nomi moslashtirildi."""
    from apps.catalog.tasks import compress_image_task

    assert compress_image_task.name == "apps.catalog.tasks.compress_image_task"
    assert celery_app.conf.task_routes["apps.catalog.tasks.compress_image_task"] == {
        "queue": "heavy"
    }


def test_task_routes_queues(celery_app):
    """Navbatlar rules.md §8.4 ga mos kelishi shart."""
    routes = celery_app.conf.task_routes
    assert routes["apps.usage.tasks.*"] == {"queue": "usage"}
    assert routes["apps.chat.tasks.*"] == {"queue": "usage"}
    assert routes["apps.usage.tasks.daily_usage_rollup"] == {"queue": "heavy"}
    assert routes["apps.chat.tasks.archive_old_conversations"] == {"queue": "heavy"}
    assert routes["apps.catalog.tasks.compress_image_task"] == {"queue": "heavy"}


def test_task_default_queue_is_default(celery_app):
    assert celery_app.conf.task_default_queue == "default"

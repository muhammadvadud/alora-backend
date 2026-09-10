from unittest.mock import patch

import pytest
from django.urls import reverse


@pytest.fixture
def url():
    return reverse("health_check")


@pytest.mark.django_db
class TestHealthCheck:
    @patch("apps.chat.health.grpc_health")
    @patch("config.health._check_database")
    @patch("config.health._check_redis")
    def test_health_all_ok(self, mock_redis, mock_db, mock_grpc, client, url):
        mock_db.return_value = {"status": "ok"}
        mock_redis.return_value = {"status": "ok"}
        mock_grpc.return_value = {"status": "ok", "version": "1.0", "active_sessions": 0}

        resp = client.get(url)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["grpc"]["status"] == "ok"

    @patch("apps.chat.health.grpc_health")
    @patch("config.health._check_database")
    @patch("config.health._check_redis")
    def test_health_grpc_failed(self, mock_redis, mock_db, mock_grpc, client, url):
        mock_db.return_value = {"status": "ok"}
        mock_redis.return_value = {"status": "ok"}
        mock_grpc.return_value = {"status": "error", "detail": "connection refused"}

        resp = client.get(url)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "degraded"
        assert data["grpc"]["status"] == "error"

    @patch("apps.chat.health.grpc_health")
    @patch("config.health._check_database")
    @patch("config.health._check_redis")
    def test_health_db_failed(self, mock_redis, mock_db, mock_grpc, client, url):
        mock_db.return_value = {"status": "error", "detail": "db down"}
        mock_redis.return_value = {"status": "ok"}
        mock_grpc.return_value = {"status": "ok"}

        resp = client.get(url)
        assert resp.status_code == 503
        data = resp.json()
        assert data["status"] == "error"
        assert data["database"]["status"] == "error"

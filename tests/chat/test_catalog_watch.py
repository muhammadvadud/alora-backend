"""Catalog Watch stream: tinchlikda heartbeat, delta kelganda uzatish."""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from apps.chat.grpc_server import catalog_service


class _FakePubSub:
    def __init__(self, messages: list) -> None:
        self._messages = messages

    def subscribe(self, *_: object) -> None:  # noqa: D401
        pass

    def unsubscribe(self) -> None:
        pass

    def close(self) -> None:
        pass

    def get_message(self, timeout: float) -> dict | None:
        if not self._messages:
            raise StopIteration  # stream tugadi (test uchun)
        return self._messages.pop(0)


def _pb2() -> SimpleNamespace:
    return SimpleNamespace(CatalogDelta=lambda **kw: kw)


def _iter(messages: list) -> list:
    fake_redis = MagicMock()
    fake_redis.pubsub.return_value = _FakePubSub(messages)
    servicer = catalog_service.CatalogServicer()
    with (
        patch.object(catalog_service, "get_catalog_version", return_value=5),
        patch.object(catalog_service.redis, "from_url", return_value=fake_redis),
    ):
        out = []
        try:
            for item in servicer._iter_deltas(5, "t1", _pb2(), heartbeat_seconds=0.01):
                out.append(item)
        except (StopIteration, RuntimeError):
            pass
        return out


def test_watch_tinchlikda_heartbeat_yuboradi() -> None:
    out = _iter([None, None])
    assert [d["entity"] for d in out] == ["heartbeat", "heartbeat"]
    assert out[0]["action"] == "PING"
    assert out[0]["version"] == 5


def test_watch_delta_uzatiladi_va_eski_versiya_tashlanadi() -> None:
    delta = {
        "version": 6, "entity": "product", "entity_id": "p1", "action": "UPSERT",
        "tenant_id": "t1", "payload_json": "{}",
    }
    old = {**delta, "version": 5}
    out = _iter([
        {"type": "subscribe"},
        {"type": "message", "data": json.dumps(old)},
        {"type": "message", "data": json.dumps(delta)},
    ])
    assert [d["entity"] for d in out] == ["product"]
    assert out[0]["version"] == 6

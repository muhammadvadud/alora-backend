"""gRPC klient testlari — retry mantiqi, deadline, AgentUnavailable.

Haqiqiy gRPC server chaqirilmaydi — hammasi mock orqali.
"""

from __future__ import annotations

import sys
from unittest import mock

import grpc
import pytest


class _StubRpcError(grpc.RpcError):
    """grpc.RpcError mock'i uchun haqiqiy subclass (code() va details() metodlar bilan)."""

    def __init__(self, code: grpc.StatusCode, detail: str) -> None:
        super().__init__(detail)
        self._code = code
        self._detail = detail

    def code(self) -> grpc.StatusCode:
        return self._code

    def details(self) -> str:
        return self._detail


def _make_rpc_error(code: grpc.StatusCode, detail: str = "mock xato") -> grpc.RpcError:
    """grpc.RpcError ga o'xshash obyekt yaratadi (except grpc.RpcError ushlay oladi)."""
    return _StubRpcError(code=code, detail=detail)


@pytest.fixture(autouse=True)
def _mock_grpc_pb(monkeypatch: pytest.MonkeyPatch) -> None:
    """grpc_gen modullarini mock qiladi — haqiqiy generatsiya talab qilinmaydi.

    `from grpc_gen import alora_pb2_grpc` importi `grpc_gen` paketining
    atributini o'qigani uchun submodullar paket atributlariga ham bog'lanadi.
    """
    package = mock.Mock()
    alora_pb2 = mock.Mock()
    alora_pb2_grpc = mock.Mock()
    package.alora_pb2 = alora_pb2
    package.alora_pb2_grpc = alora_pb2_grpc
    sys.modules["grpc_gen"] = package
    sys.modules["grpc_gen.alora_pb2"] = alora_pb2
    sys.modules["grpc_gen.alora_pb2_grpc"] = alora_pb2_grpc
    yield
    for name in ("grpc_gen", "grpc_gen.alora_pb2", "grpc_gen.alora_pb2_grpc"):
        sys.modules.pop(name, None)


@pytest.fixture(autouse=True)
def _mock_channel_pool(monkeypatch: pytest.MonkeyPatch) -> None:
    """Kanal pool'ini mock qiladi — haqiqiy soket ochilmaydi."""
    from apps.chat import grpc_client

    mock_channel = mock.Mock(spec=grpc.Channel)
    mock_channel.close = mock.Mock()

    patcher = mock.patch.object(grpc_client, "get_agent_channel", return_value=mock_channel)
    patcher.start()
    yield
    patcher.stop()


def _agent_stub() -> mock.Mock:
    """AgentStub ni mock qilib qaytaradi."""
    stub = mock.Mock()
    sys.modules["grpc_gen.alora_pb2_grpc"].AgentStub.return_value = stub
    return stub


class TestChatRetry:
    def test_unavailable_retries_then_succeeds(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """UNAVAILABLE xatosi qayta uriniladi, keyin muvaffaqiyat."""
        from apps.chat import grpc_client

        stub = _agent_stub()
        stub.Chat.side_effect = [
            _make_rpc_error(grpc.StatusCode.UNAVAILABLE),
            _make_rpc_error(grpc.StatusCode.UNAVAILABLE),
            [mock.Mock()],
        ]
        monkeypatch.setattr(grpc_client.time, "sleep", lambda _: None)

        events = list(
            grpc_client.chat_stream(
                session_id="s1",
                user_id="u1",
                tenant_id="t1",
                message="Salom",
            )
        )

        assert len(events) == 1
        assert stub.Chat.call_count == 3

    def test_timeout_raises_agent_timeout(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """DEADLINE_EXCEEDED qayta uriniladi, keyin AgentTimeout ko'tariladi."""
        from apps.chat import grpc_client
        from apps.chat.exceptions import AgentTimeout

        stub = _agent_stub()
        stub.Chat.side_effect = _make_rpc_error(grpc.StatusCode.DEADLINE_EXCEEDED)
        monkeypatch.setattr(grpc_client.time, "sleep", lambda _: None)

        with pytest.raises(AgentTimeout):
            list(
                grpc_client.chat_stream(
                    session_id="s1",
                    user_id="u1",
                    tenant_id="t1",
                    message="Salom",
                )
            )

        assert stub.Chat.call_count == 3

    def test_unavailable_raises_agent_unavailable(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """UNAVAILABLE 3 marta bo'lsa — AgentUnavailable ko'tariladi."""
        from apps.chat import grpc_client
        from apps.chat.exceptions import AgentUnavailable

        stub = _agent_stub()
        stub.Chat.side_effect = _make_rpc_error(grpc.StatusCode.UNAVAILABLE)
        monkeypatch.setattr(grpc_client.time, "sleep", lambda _: None)

        with pytest.raises(AgentUnavailable):
            list(
                grpc_client.chat_stream(
                    session_id="s1",
                    user_id="u1",
                    tenant_id="t1",
                    message="Salom",
                )
            )

        assert stub.Chat.call_count == 3

    def test_non_retryable_error_raises_immediately(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Retry qilinmaydigan xato (INVALID_ARGUMENT) — darhol ko'tariladi."""
        from apps.chat import grpc_client

        stub = _agent_stub()
        stub.Chat.side_effect = _make_rpc_error(grpc.StatusCode.INVALID_ARGUMENT)
        monkeypatch.setattr(grpc_client.time, "sleep", lambda _: None)

        with pytest.raises(grpc.RpcError):
            list(
                grpc_client.chat_stream(
                    session_id="s1",
                    user_id="u1",
                    tenant_id="t1",
                    message="Salom",
                )
            )

        assert stub.Chat.call_count == 1

    def test_exponential_backoff_sleep_increases(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Backoff vaqtlari o'sib borishi tekshiriladi."""
        from apps.chat import grpc_client

        stub = _agent_stub()
        stub.Chat.side_effect = [
            _make_rpc_error(grpc.StatusCode.UNAVAILABLE),
            _make_rpc_error(grpc.StatusCode.UNAVAILABLE),
            [mock.Mock()],
        ]
        sleeps: list[float] = []
        monkeypatch.setattr(grpc_client.time, "sleep", sleeps.append)

        list(
            grpc_client.chat_stream(
                session_id="s1",
                user_id="u1",
                tenant_id="t1",
                message="Salom",
            )
        )

        assert len(sleeps) == 2
        assert sleeps[1] > sleeps[0]


class TestDeadline:
    def test_chat_stream_passes_deadline(self) -> None:
        """Chatga deadline uzatiladi."""
        from apps.chat import grpc_client

        stub = _agent_stub()
        stub.Chat.return_value = [mock.Mock()]

        list(
            grpc_client.chat_stream(
                session_id="s1",
                user_id="u1",
                tenant_id="t1",
                message="Salom",
                deadline_seconds=30.0,
            )
        )

        assert stub.Chat.call_args is not None
        call_kwargs = stub.Chat.call_args.kwargs
        assert call_kwargs["timeout"] == 30.0

    def test_voice_chat_uses_deadline(self) -> None:
        """VoiceChat deadline qo'llaydi."""
        from apps.chat import grpc_client

        stub = _agent_stub()
        stub.VoiceChat.return_value = [mock.Mock()]

        list(grpc_client.voice_chat_stream(chunks=iter([])))

        assert stub.VoiceChat.call_args is not None
        call_kwargs = stub.VoiceChat.call_args.kwargs
        assert call_kwargs["timeout"] == 120.0


class TestHealthCheck:
    def test_health_ok(self) -> None:
        """Health muvaffaqiyatli bo'lsa holat qaytaradi."""
        from apps.chat import grpc_client

        response = mock.Mock()
        response.status = "ok"
        response.version = "1.0.0"
        response.active_sessions = 3
        response.last_error = ""

        stub = _agent_stub()
        stub.Health.return_value = response

        result = grpc_client.health_check()

        assert result["status"] == "ok"
        assert result["version"] == "1.0.0"
        assert result["active_sessions"] == 3

    def test_health_unavailable(self) -> None:
        """Health xato bersa — unavailable holati qaytariladi."""
        from apps.chat import grpc_client

        stub = _agent_stub()
        stub.Health.side_effect = _make_rpc_error(grpc.StatusCode.UNAVAILABLE)

        result = grpc_client.health_check()

        assert result["status"] == "unavailable"


class TestResetSession:
    def test_reset_session_success(self) -> None:
        """ResetSession muvaffaqiyatli chaqiriladi."""
        from apps.chat import grpc_client

        response = mock.Mock()
        response.success = True
        response.message = ""

        stub = _agent_stub()
        stub.ResetSession.return_value = response

        result = grpc_client.reset_session(session_id="s1", user_id="u1")

        assert result.success is True

    def test_reset_session_unavailable(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """ResetSession UNAVAILABLE bo'lsa — AgentUnavailable."""
        from apps.chat import grpc_client
        from apps.chat.exceptions import AgentUnavailable

        stub = _agent_stub()
        stub.ResetSession.side_effect = _make_rpc_error(grpc.StatusCode.UNAVAILABLE)
        monkeypatch.setattr(grpc_client.time, "sleep", lambda _: None)

        with pytest.raises(AgentUnavailable):
            grpc_client.reset_session(session_id="s1", user_id="u1")

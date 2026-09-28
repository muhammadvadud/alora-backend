"""gRPC bootstrap va service-token interceptor testlari."""

from __future__ import annotations

from unittest import mock
from unittest.mock import Mock

import grpc
import pytest

from apps.chat.grpc_server.auth import ServiceTokenInterceptor, tokens_match


def test_service_token_interceptor_rejects_missing_token(settings: object) -> None:
    """Token bo'lmasa RPC UNAUTHENTICATED bilan tugaydi."""

    settings.DEBUG = False
    settings.AGENT_SERVICE_TOKEN = "secret"
    implementation = Mock(return_value="ok")
    handler = grpc.unary_unary_rpc_method_handler(implementation)
    details = Mock(invocation_metadata=())
    wrapped = ServiceTokenInterceptor().intercept_service(lambda _: handler, details)
    context = Mock()

    wrapped.unary_unary(None, context)

    context.abort.assert_called_once_with(
        grpc.StatusCode.UNAUTHENTICATED, "service token noto'g'ri"
    )


def test_service_token_interceptor_allows_correct_token(settings: object) -> None:
    """To'g'ri service token RPC'ni davom ettiradi."""

    settings.DEBUG = False
    settings.AGENT_SERVICE_TOKEN = "secret"
    implementation = Mock(return_value="ok")
    handler = grpc.unary_unary_rpc_method_handler(implementation)
    details = Mock(invocation_metadata=(("x-service-token", "secret"),))
    wrapped = ServiceTokenInterceptor().intercept_service(lambda _: handler, details)

    assert wrapped.unary_unary(None, Mock()) == "ok"


class _AbortingContext:
    """`context.abort` haqiqatdagidek istisno tashlaydigan mock kontekst."""

    def __init__(self) -> None:
        self.aborted: tuple[object, object] | None = None

    def abort(self, code: object, details: object) -> None:
        self.aborted = (code, details)
        raise RuntimeError(f"aborted: {code} {details}")


def test_service_token_interceptor_rejects_wrong_token(settings: object) -> None:
    """Noto'g'ri token UNAUTHENTICATED bilan rad etiladi."""

    settings.DEBUG = False
    settings.AGENT_SERVICE_TOKEN = "secret"
    implementation = Mock(return_value="ok")
    handler = grpc.unary_unary_rpc_method_handler(implementation)
    details = Mock(invocation_metadata=(("x-service-token", "secre7"),))
    wrapped = ServiceTokenInterceptor().intercept_service(lambda _: handler, details)
    context = _AbortingContext()

    with pytest.raises(RuntimeError):
        wrapped.unary_unary(None, context)

    assert context.aborted == (grpc.StatusCode.UNAUTHENTICATED, "service token noto'g'ri")
    implementation.assert_not_called()


def test_service_token_comparison_uses_constant_time_helper(settings: object) -> None:
    """Interceptor solishtirishni `tokens_match` (hmac.compare_digest) orqali qiladi."""

    settings.DEBUG = False
    settings.AGENT_SERVICE_TOKEN = "secret"
    handler = grpc.unary_unary_rpc_method_handler(Mock(return_value="ok"))
    details = Mock(invocation_metadata=(("x-service-token", "secre7"),))

    with mock.patch("apps.chat.grpc_server.auth.tokens_match", return_value=False) as compare:
        wrapped = ServiceTokenInterceptor().intercept_service(lambda _: handler, details)
        with pytest.raises(RuntimeError):
            wrapped.unary_unary(None, _AbortingContext())

    compare.assert_called_once_with("secre7", "secret")


class TestTokensMatch:
    """`tokens_match` — `hmac.compare_digest` bilan vaqtga bog'liq bo'lmagan solishtirish."""

    def test_equal_tokens_match(self) -> None:
        assert tokens_match("secret", "secret") is True

    def test_different_tokens_do_not_match(self) -> None:
        assert tokens_match("secre7", "secret") is False

    def test_prefix_token_does_not_match(self) -> None:
        """Qisqa tasodifiy to'g'ri kelish ham qabul qilinmasligi kerak."""

        assert tokens_match("sec", "secret") is False

    def test_empty_and_missing_token_do_not_match(self) -> None:
        assert tokens_match("", "secret") is False
        assert tokens_match(None, "secret") is False

    def test_empty_expected_token_never_matches(self) -> None:
        """Token sozlanmagan bo'lsa tokensiz so'rov o'tmaydi (fail-closed)."""

        assert tokens_match("", "") is False
        assert tokens_match(None, None) is False
        assert tokens_match(None, "") is False
        assert tokens_match("anything", "") is False


def test_run_grpc_registers_all_servicers(
    monkeypatch: pytest.MonkeyPatch, settings: object
) -> None:
    """Management command uchta servisni serverga ro'yxatdan o'tkazadi."""

    from apps.chat.management.commands import run_grpc

    settings.DEBUG = True
    settings.AGENT_SERVICE_TOKEN = ""
    server = Mock()
    server.add_insecure_port.return_value = 1
    monkeypatch.setattr(run_grpc.grpc, "server", Mock(return_value=server))
    monkeypatch.setattr(run_grpc.alora_pb2_grpc, "add_CatalogServicer_to_server", Mock())
    monkeypatch.setattr(run_grpc.alora_pb2_grpc, "add_BackendServicer_to_server", Mock())
    monkeypatch.setattr(run_grpc.alora_pb2_grpc, "add_PricingServicer_to_server", Mock())
    server.wait_for_termination.side_effect = KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        run_grpc.Command().handle()

    run_grpc.alora_pb2_grpc.add_CatalogServicer_to_server.assert_called_once()
    run_grpc.alora_pb2_grpc.add_BackendServicer_to_server.assert_called_once()
    run_grpc.alora_pb2_grpc.add_PricingServicer_to_server.assert_called_once()
    server.add_insecure_port.assert_called_once_with("[::]:9091")

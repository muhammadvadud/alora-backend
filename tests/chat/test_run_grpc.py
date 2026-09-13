"""gRPC bootstrap va service-token interceptor testlari."""

from __future__ import annotations

from unittest.mock import Mock

import grpc
import pytest

from apps.chat.grpc_server.auth import ServiceTokenInterceptor


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

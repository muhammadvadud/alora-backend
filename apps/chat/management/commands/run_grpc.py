"""Django ichida Catalog, Backend va Pricing gRPC serverini ishga tushiradi."""

from __future__ import annotations

import signal
from concurrent import futures

import grpc
import structlog
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.chat.grpc_server.auth import ServiceTokenInterceptor
from apps.chat.grpc_server.backend_service import BackendServicer
from apps.chat.grpc_server.catalog_service import CatalogServicer
from apps.chat.grpc_server.pricing_service import PricingServicer
from grpc_gen import alora_pb2_grpc

logger = structlog.get_logger(__name__)


class Command(BaseCommand):
    """Ichki gRPC serverini 9091 portida ishga tushiruvchi command."""

    help = "Alora ichki gRPC serverini ishga tushirish"

    def handle(self, *args: object, **options: object) -> None:
        token = getattr(settings, "AGENT_SERVICE_TOKEN", "")
        if not token and not settings.DEBUG:
            raise CommandError("AGENT_SERVICE_TOKEN prod muhitida bo'sh bo'lishi mumkin emas")

        server = grpc.server(
            futures.ThreadPoolExecutor(max_workers=getattr(settings, "GRPC_MAX_WORKERS", 16)),
            interceptors=[ServiceTokenInterceptor()],
        )
        alora_pb2_grpc.add_CatalogServicer_to_server(CatalogServicer(), server)
        alora_pb2_grpc.add_BackendServicer_to_server(BackendServicer(), server)
        alora_pb2_grpc.add_PricingServicer_to_server(PricingServicer(), server)
        port = getattr(settings, "GRPC_PORT", 9091)
        server.add_insecure_port(f"[::]:{port}")
        server.start()
        logger.info("gRPC server ishga tushdi", port=port)

        def stop(signum: int, frame: object) -> None:
            logger.info("gRPC server to'xtatilmoqda", signal=signum)
            server.stop(10).wait()

        signal.signal(signal.SIGTERM, stop)
        signal.signal(signal.SIGINT, stop)
        server.wait_for_termination()

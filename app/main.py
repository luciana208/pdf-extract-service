import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.formparsers import MultiPartParser

from app.config.settings import settings
from app.data.extractors.process_pool_extractor import ProcessPoolTextExtractor
from app.infrastructure.consul_registry import ConsulRegistry, build_consul_client
from app.infrastructure.health import HealthReporter
from app.infrastructure.in_flight import in_flight
from app.infrastructure.instance import INSTANCE_ID
from app.presentation.error_handlers import register_error_handlers
from app.presentation.middlewares.body_size_limit import BodySizeLimitMiddleware
from app.presentation.middlewares.in_flight import InFlightMiddleware
from app.presentation.routers.extraction_router import router as extraction_router
from app.presentation.routers.health_router import router as health_router

# logs a stdout (12-factor xi)
logging.basicConfig(
    stream=sys.stdout,
    level=settings.log_level.upper(),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

# margen para boundaries y headers del multipart
REQUEST_OVERHEAD_BYTES = 64 * 1024
MAX_REQUEST_BYTES = settings.max_pdf_size_bytes + REQUEST_OVERHEAD_BYTES

# el pdf no se escribe a disco: starlette solo pasa a archivo temporal lo que supera este umbral
MultiPartParser.spool_max_size = MAX_REQUEST_BYTES


@asynccontextmanager
async def lifespan(app: FastAPI):
    extractor = ProcessPoolTextExtractor(
        workers=settings.extract_workers,
        max_in_flight=settings.max_in_flight,
        retry_after_seconds=settings.saturated_retry_after_seconds,
    )
    app.state.extractor = extractor
    app.state.health = HealthReporter(in_flight)
    registry = None
    consul_client = None
    if settings.consul_enabled:
        consul_client = build_consul_client(settings)
        registry = ConsulRegistry(settings, consul_client, INSTANCE_ID)
        registry.start()
    yield
    # cierre ordenado: salir de consul, terminar lo que esta en curso y cerrar el pool
    if registry:
        await registry.stop()
    if consul_client:
        await consul_client.aclose()
    extractor.shutdown()


def create_app() -> FastAPI:
    app = FastAPI(title=settings.service_name, version=settings.service_version, lifespan=lifespan)
    app.add_middleware(BodySizeLimitMiddleware, max_bytes=MAX_REQUEST_BYTES)
    app.add_middleware(InFlightMiddleware, counter=in_flight)
    register_error_handlers(app)
    app.include_router(health_router)
    app.include_router(extraction_router)
    return app


app = create_app()

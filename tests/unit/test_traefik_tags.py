from app.config.settings import Settings
from app.infrastructure.traefik_tags import build_traefik_tags


def test_router_interno_con_circuit_breaker_y_reintentos():
    tags = build_traefik_tags(Settings(router_name="extract", internal_host="extract.internal", public_host=""))
    assert "traefik.enable=true" in tags
    assert "traefik.http.routers.extract-internal.rule=Host(`extract.internal`)" in tags
    assert "traefik.http.routers.extract-internal.entrypoints=internal" in tags
    assert "traefik.http.routers.extract-internal.middlewares=extract-cb,extract-retry" in tags
    assert any(tag.startswith("traefik.http.middlewares.extract-cb.circuitbreaker.expression=") for tag in tags)
    assert "traefik.http.middlewares.extract-retry.retry.attempts=3" in tags


def test_sin_host_publico_no_hay_router_https():
    tags = build_traefik_tags(Settings(router_name="extract", public_host=""))
    assert not any(".routers.extract.rule" in tag for tag in tags)


def test_con_host_publico_agrega_router_https_con_tls():
    tags = build_traefik_tags(Settings(router_name="extract", public_host="extract.pdfextractext.localhost"))
    assert "traefik.http.routers.extract.entrypoints=https" in tags
    assert "traefik.http.routers.extract.tls=true" in tags

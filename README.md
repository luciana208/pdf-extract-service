# pdf-extract-service

Microservicio de **extracción** de PDF-extractext. Recibe un PDF y devuelve su contenido en **Markdown** (por defecto) o en **texto plano**, junto con la cantidad de páginas.

Cumple dos roles:

- Paso de extracción de la Saga del proyecto: el orquestador pide `format=text`, porque la Etapa 1 pide solo el texto.
- Microservicio del **TP de Test de Carga y Stress**: `POST /extract` con la respuesta `{"content", "page_count"}` que pide la consigna.

## Endpoint

`POST /extract?format=markdown|text`

El PDF puede ir como `multipart/form-data` (campo `file`) o como body binario (`application/pdf`).

```json
{"content": "# Titulo\n\ntexto…", "page_count": 292}
```

| Status | Cuándo |
|---|---|
| `200` | OK |
| `400` | No es un PDF, está dañado o protegido |
| `413` | Supera `MAX_PDF_SIZE_MB` |
| `422` | `format` desconocido |
| `503` + `Retry-After` | El servicio está saturado (backpressure) |

`GET /health`: estado de la instancia.

## Rendimiento y concurrencia

- **Runtime HTTP separado de la extracción:** Granian atiende HTTP y la extracción corre en un pool de `EXTRACT_WORKERS` procesos (`ProcessPoolExecutor`), así un PDF pesado no bloquea el event loop.
- **Backpressure:** con `MAX_IN_FLIGHT` extracciones en curso, la siguiente recibe `503` con `Retry-After` al instante, en vez de esperar en una cola hasta vencer el timeout del cliente.
- **Sin disco:** el PDF se procesa en memoria. El umbral de spool de Starlette se sube al tamaño máximo para que el multipart no se escriba en un archivo temporal.
- **Markdown liviano:** conversor propio (`app/data/extractors/markdown_writer.py`) que lee cada página una sola vez con `get_text("dict")`; el tamaño de letra con más texto es el cuerpo y los tres mayores pasan a ser títulos `#`, `##` y `###`. Reemplazó a `pymupdf4llm`, que tardaba unas 18 veces más porque arma el texto de cada página dos veces y detecta columnas, listas y tablas. No reconoce columnas, listas ni tablas.

## Arquitectura

```
presentation   extraction_router · lectura multipart/binario · controller · DTO · errores RFC 9457
use_cases      ExtractTextUseCase: revalida tamaño y firma (no confia en otros servicios) y extrae
business       OutputFormat · ExtractionResult · reglas · puerto ITextExtractor
data           ProcessPoolTextExtractor (pool + backpressure) · pymupdf_extraction (dentro del proceso)
infrastructure Consul · tags de Traefik · health · instancia
```

## Configuración

Ver `.env.example`. Las propias de este servicio:

| Variable | Por defecto | Descripción |
|---|---|---|
| `MAX_PDF_SIZE_MB` | `10` | Tamaño máximo |
| `EXTRACT_WORKERS` | `1` | Procesos de extracción por réplica |
| `MAX_IN_FLIGHT` | `8` | Extracciones aceptadas a la vez antes de responder 503 |
| `SATURATED_RETRY_AFTER_SECONDS` | `2` | Valor del header `Retry-After` |
| `PUBLIC_HOST` | `extract.pdfextractext.localhost` | Host HTTPS (para el TP de carga) |
| `INTERNAL_HOST` | `extract.internal` | Nombre interno en Traefik |

## Desarrollo

```bash
uv sync
uv run pytest
GRANIAN_INTERFACE=asgi EXTRACT_WORKERS=2 uv run granian app.main:app --port 8002
curl -s -F file=@documento.pdf "localhost:8002/extract?format=markdown"
```

Las pruebas de carga (k6 y Vegeta) están en `pdf-extractext-deploy/tests/stress`.

## Nota sobre licencias

La extracción usa [PyMuPDF](https://github.com/pymupdf/PyMuPDF), que se distribuye bajo **AGPL-3.0** (o licencia comercial de Artifex). Este repo es MIT, pero una imagen que incluye PyMuPDF queda alcanzada por la AGPL: si se distribuye o se ofrece como servicio, el código fuente tiene que estar disponible. Para un trabajo académico con repositorio público eso ya se cumple. Para un uso comercial habría que comprar la licencia de Artifex o cambiar a una librería con licencia permisiva (pypdfium2, pdfplumber), a costa de rendimiento y de la salida en Markdown.

## Plataforma (igual en los cuatro servicios)

| Pieza | Archivo | Qué hace |
|---|---|---|
| Registro en Consul | `app/infrastructure/consul_registry.py` | Al arrancar registra la instancia con ID único (`<servicio>-<hex>`), su IP, el check HTTP a `/health` y los tags de Traefik. Si Consul no está, reintenta en segundo plano. Al apagarse se da de baja. |
| Tags de Traefik | `app/infrastructure/traefik_tags.py` | Routers interno y público, circuit breaker y reintentos |
| Health | `app/infrastructure/health.py` | Contrato común: `status`, `service`, `version`, `instance_id`, `uptime_seconds`, `memory_mb`, `requests_in_flight`, `dependencies` |
| Errores | `app/presentation/error_handlers.py` | Todo error sale en formato RFC 9457 (`application/problem+json`) |

## Ejecución dentro del sistema completo

Este servicio no se levanta solo en producción: lo levanta `pdf-extractext-deploy` junto con Traefik, Consul y el resto de los servicios.

```bash
cd ../pdf-extractext-deploy
./scripts/up.sh
```

## Imagen Docker

- Multi-stage: `uv` solo está en la etapa de build; la imagen final tiene Python 3.14 slim, el venv y el código.
- Usuario sin privilegios (`appuser`) y zona horaria `America/Argentina/Buenos_Aires`.
- `HEALTHCHECK` contra `/health`.
- Granian toma host, puerto y workers de `GRANIAN_*`, así que el puerto no queda fijo en la imagen.

```bash
docker build -t pdf-extractext/extract:1.0.0 .
```

## Principios aplicados

- **Arquitectura limpia / puertos y adaptadores:** el negocio depende de interfaces y `app/dependencies.py` elige las implementaciones.
- **SOLID, DRY, KISS, YAGNI:** un caso de uso por operación, sin dependencias que no se usan.
- **TDD:** cada cambio arranca con un test que falla.
- **12-Factor:** un repo por servicio (I), dependencias fijadas con `uv.lock` (II), configuración por entorno (III), servicios externos por URL (IV), build y run separados (V), procesos sin estado (VI), port binding (VII), apagado ordenado (IX), logs a stdout (XI).

## Equipo

Fabio, Luciana y Celina — Desarrollo de Software, UTN Facultad Regional San Rafael, 2026.

## Licencia

MIT, ver [LICENSE](LICENSE).

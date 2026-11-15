from tests.pdf_factory import CORRUPT_PDF, NOT_A_PDF, TEXT_PDF, build_pdf

PDF_HEADERS = {"Content-Type": "application/pdf"}


async def test_multipart_devuelve_content_y_page_count(client):
    response = await client.post("/extract", files={"file": ("doc.pdf", TEXT_PDF, "application/pdf")})
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"content", "page_count"}
    assert "Hola Mundo PDF" in body["content"]
    assert body["page_count"] == 1


async def test_body_binario_tambien_funciona(client):
    response = await client.post("/extract", content=TEXT_PDF, headers=PDF_HEADERS)
    assert response.status_code == 200
    assert "Hola Mundo PDF" in response.json()["content"]


async def test_formato_texto(client):
    response = await client.post("/extract?format=text", content=build_pdf(["uno", "dos"]), headers=PDF_HEADERS)
    assert response.status_code == 200
    assert response.json()["page_count"] == 2


async def test_formato_desconocido_devuelve_422(client):
    response = await client.post("/extract?format=html", content=TEXT_PDF, headers=PDF_HEADERS)
    assert response.status_code == 422
    assert response.headers["content-type"] == "application/problem+json"


async def test_multipart_sin_campo_file_devuelve_400(client):
    response = await client.post("/extract", files={"otro": ("doc.pdf", TEXT_PDF, "application/pdf")})
    assert response.status_code == 400


async def test_no_pdf_devuelve_400(client):
    response = await client.post("/extract", content=NOT_A_PDF, headers=PDF_HEADERS)
    assert response.status_code == 400


async def test_pdf_dañado_devuelve_400(client):
    response = await client.post("/extract", content=CORRUPT_PDF, headers=PDF_HEADERS)
    assert response.status_code == 400


async def test_pdf_muy_grande_devuelve_413(client):
    response = await client.post("/extract", content=build_pdf(padding=2 * 1024 * 1024), headers=PDF_HEADERS)
    assert response.status_code == 413


async def test_saturado_devuelve_503_con_retry_after(client):
    client.app_state.extractor._max_in_flight = 0
    response = await client.post("/extract", content=TEXT_PDF, headers=PDF_HEADERS)
    assert response.status_code == 503
    assert response.headers["retry-after"] == "2"
    assert response.headers["content-type"] == "application/problem+json"


async def test_health_responde_ok(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["service"] == "pdf-extract-service"

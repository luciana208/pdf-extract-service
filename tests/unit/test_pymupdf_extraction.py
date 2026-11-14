import pytest

from app.business.domain.exceptions import InvalidPDFError
from app.business.entities.extraction import OutputFormat
from app.data.extractors.pymupdf_extraction import extract_document
from tests.pdf_factory import CORRUPT_PDF, build_pdf


def test_texto_plano_devuelve_contenido_y_paginas():
    content, page_count = extract_document(build_pdf(["Hola Mundo PDF", "Segunda pagina"]), OutputFormat.TEXT)
    assert "Hola Mundo PDF" in content
    assert "Segunda pagina" in content
    assert page_count == 2


def test_markdown_devuelve_el_texto():
    content, page_count = extract_document(build_pdf(["Hola Mundo PDF"]), OutputFormat.MARKDOWN)
    assert "Hola Mundo PDF" in content
    assert page_count == 1


def test_pdf_sin_texto_devuelve_contenido_vacio():
    content, page_count = extract_document(build_pdf([""]), OutputFormat.TEXT)
    assert content == ""
    assert page_count == 1


def test_pdf_dañado_lanza_invalid_pdf():
    with pytest.raises(InvalidPDFError):
        extract_document(CORRUPT_PDF, OutputFormat.TEXT)

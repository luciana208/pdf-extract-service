import pytest

from app.business.domain.exceptions import InvalidPDFError, PDFTooLargeError
from app.business.entities.extraction import ExtractionResult, OutputFormat
from app.business.extractors.interfaces.i_text_extractor import ITextExtractor
from app.use_cases.extract_text import ExtractTextUseCase
from tests.pdf_factory import NOT_A_PDF, TEXT_PDF


class FakeExtractor(ITextExtractor):
    def __init__(self) -> None:
        self.calls: list[OutputFormat] = []

    async def extract(self, file_bytes: bytes, output_format: OutputFormat) -> ExtractionResult:
        self.calls.append(output_format)
        return ExtractionResult(content="contenido", page_count=1)


async def test_delega_en_el_extractor_con_el_formato_pedido():
    extractor = FakeExtractor()
    result = await ExtractTextUseCase(extractor, 10_000).execute(TEXT_PDF, OutputFormat.TEXT)
    assert result == ExtractionResult(content="contenido", page_count=1)
    assert extractor.calls == [OutputFormat.TEXT]


async def test_no_extrae_si_no_es_pdf():
    extractor = FakeExtractor()
    with pytest.raises(InvalidPDFError):
        await ExtractTextUseCase(extractor, 10_000).execute(NOT_A_PDF, OutputFormat.TEXT)
    assert extractor.calls == []


async def test_no_extrae_si_supera_el_tamaño():
    extractor = FakeExtractor()
    with pytest.raises(PDFTooLargeError):
        await ExtractTextUseCase(extractor, 10).execute(TEXT_PDF, OutputFormat.TEXT)
    assert extractor.calls == []

import asyncio

import pytest

from app.business.domain.exceptions import ExtractorSaturatedError, InvalidPDFError
from app.business.entities.extraction import OutputFormat
from app.data.extractors.process_pool_extractor import ProcessPoolTextExtractor
from tests.pdf_factory import CORRUPT_PDF, TEXT_PDF


@pytest.fixture
def extractor():
    pool = ProcessPoolTextExtractor(workers=1, max_in_flight=2, retry_after_seconds=3)
    yield pool
    pool.shutdown()


async def test_extrae_en_otro_proceso(extractor):
    result = await extractor.extract(TEXT_PDF, OutputFormat.TEXT)
    assert "Hola Mundo PDF" in result.content
    assert result.page_count == 1
    assert extractor.in_flight == 0


async def test_error_del_proceso_llega_como_invalid_pdf(extractor):
    with pytest.raises(InvalidPDFError):
        await extractor.extract(CORRUPT_PDF, OutputFormat.TEXT)
    assert extractor.in_flight == 0


async def test_rechaza_cuando_supera_el_maximo_en_curso(extractor):
    tasks = [asyncio.create_task(extractor.extract(TEXT_PDF, OutputFormat.TEXT)) for _ in range(2)]
    await asyncio.sleep(0)
    with pytest.raises(ExtractorSaturatedError) as error:
        await extractor.extract(TEXT_PDF, OutputFormat.TEXT)
    assert error.value.retry_after_seconds == 3
    await asyncio.gather(*tasks)

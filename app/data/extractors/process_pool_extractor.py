"""adaptador de ITextExtractor que separa la extraccion del runtime http en un pool de procesos"""

import asyncio
import logging
from concurrent.futures import ProcessPoolExecutor

from app.business.domain.exceptions import ExtractorSaturatedError
from app.business.entities.extraction import ExtractionResult, OutputFormat
from app.business.extractors.interfaces.i_text_extractor import ITextExtractor
from app.data.extractors.pymupdf_extraction import extract_document

logger = logging.getLogger(__name__)


class ProcessPoolTextExtractor(ITextExtractor):
    def __init__(self, workers: int, max_in_flight: int, retry_after_seconds: int) -> None:
        self._pool = ProcessPoolExecutor(max_workers=workers)
        self._max_in_flight = max_in_flight
        self._retry_after_seconds = retry_after_seconds
        self._in_flight = 0

    @property
    def in_flight(self) -> int:
        return self._in_flight

    async def extract(self, file_bytes: bytes, output_format: OutputFormat) -> ExtractionResult:
        # backpressure: si la cola esta llena se rechaza enseguida con 503
        if self._in_flight >= self._max_in_flight:
            logger.warning("extraccion rechazada por saturacion (%s en curso)", self._in_flight)
            raise ExtractorSaturatedError(self._retry_after_seconds)

        self._in_flight += 1
        try:
            loop = asyncio.get_running_loop()
            content, page_count = await loop.run_in_executor(
                self._pool, extract_document, file_bytes, output_format.value
            )
        finally:
            self._in_flight -= 1
        return ExtractionResult(content=content, page_count=page_count)

    def shutdown(self) -> None:
        # espera las extracciones en curso y descarta las que no arrancaron
        self._pool.shutdown(wait=True, cancel_futures=True)

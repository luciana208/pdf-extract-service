from app.business.domain.pdf_rules import ensure_pdf_signature, ensure_within_size
from app.business.entities.extraction import ExtractionResult, OutputFormat
from app.business.extractors.interfaces.i_text_extractor import ITextExtractor


class ExtractTextUseCase:
    """revalida lo minimo (no confia en otros servicios) y extrae"""

    def __init__(self, extractor: ITextExtractor, max_size_bytes: int) -> None:
        self._extractor = extractor
        self._max_size_bytes = max_size_bytes

    async def execute(self, file_bytes: bytes, output_format: OutputFormat) -> ExtractionResult:
        ensure_within_size(file_bytes, self._max_size_bytes)
        ensure_pdf_signature(file_bytes)
        return await self._extractor.extract(file_bytes, output_format)

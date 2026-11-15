from app.business.entities.extraction import OutputFormat
from app.presentation.dto.response.extraction_response import ExtractionResponseDTO
from app.use_cases.extract_text import ExtractTextUseCase


class ExtractionController:
    """traduce entre http y el caso de uso"""

    def __init__(self, extract_text: ExtractTextUseCase) -> None:
        self._extract_text = extract_text

    async def extract(self, file_bytes: bytes, output_format: OutputFormat) -> ExtractionResponseDTO:
        result = await self._extract_text.execute(file_bytes, output_format)
        return ExtractionResponseDTO.from_entity(result)

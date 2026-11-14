from abc import ABC, abstractmethod

from app.business.entities.extraction import ExtractionResult, OutputFormat


class ITextExtractor(ABC):
    """puerto de extraccion, el negocio no sabe con que libreria ni en que proceso corre"""

    @abstractmethod
    async def extract(self, file_bytes: bytes, output_format: OutputFormat) -> ExtractionResult:
        """
        devuelve el contenido y la cantidad de paginas.
        lanza InvalidPDFError si no se puede leer y ExtractorSaturatedError si no hay lugar.
        """

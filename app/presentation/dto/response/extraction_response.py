"""contrato de salida de /extract (el que pide el tp de carga)"""

from pydantic import BaseModel, Field

from app.business.entities.extraction import ExtractionResult


class ExtractionResponseDTO(BaseModel):
    content: str = Field(description="Contenido extraido en markdown o texto plano.")
    page_count: int = Field(description="Cantidad de paginas del PDF.")

    model_config = {"frozen": True}

    @classmethod
    def from_entity(cls, result: ExtractionResult) -> "ExtractionResponseDTO":
        return cls(content=result.content, page_count=result.page_count)

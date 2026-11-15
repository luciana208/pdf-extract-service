"""endpoint de extraccion: POST /extract?format=markdown|text"""

from fastapi import APIRouter, Depends, Query, Request, status

from app.business.entities.extraction import OutputFormat
from app.dependencies import get_extraction_controller
from app.presentation.controllers.extraction_controller import ExtractionController
from app.presentation.dto.response.extraction_response import ExtractionResponseDTO
from app.presentation.pdf_body import read_pdf_bytes

router = APIRouter(tags=["extraction"])

# acepta las dos formas que pide la consigna del tp de carga
PDF_BODY = {
    "requestBody": {
        "required": True,
        "content": {
            "multipart/form-data": {
                "schema": {"type": "object", "properties": {"file": {"type": "string", "format": "binary"}}, "required": ["file"]}
            },
            "application/pdf": {"schema": {"type": "string", "format": "binary"}},
        },
    }
}


@router.post(
    "/extract",
    response_model=ExtractionResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Extraer el contenido de un PDF",
    openapi_extra=PDF_BODY,
)
async def extract(
    request: Request,
    output_format: OutputFormat = Query(OutputFormat.MARKDOWN, alias="format", description="markdown o text"),
    controller: ExtractionController = Depends(get_extraction_controller),
) -> ExtractionResponseDTO:
    """
    extrae el contenido en markdown (por defecto) o texto plano.
    errores: 400 pdf invalido, 413 muy grande, 422 formato desconocido, 503 saturado.
    """
    file_bytes = await read_pdf_bytes(request)
    return await controller.extract(file_bytes, output_format)

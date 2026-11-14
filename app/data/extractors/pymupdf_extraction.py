"""extraccion con pymupdf; corre dentro de los procesos del pool, por eso son funciones sueltas"""

import pymupdf
import pymupdf4llm

from app.business.domain.exceptions import InvalidPDFError
from app.business.entities.extraction import OutputFormat

# sin el motor de layout ni ocr: mucho mas rapido y alcanza para pdfs con texto
pymupdf4llm.use_layout(False)
pymupdf.TOOLS.mupdf_display_errors(False)


def extract_document(file_bytes: bytes, output_format: str) -> tuple[str, int]:
    try:
        document = pymupdf.open(stream=file_bytes, filetype="pdf")
    except (pymupdf.FileDataError, RuntimeError, ValueError) as exc:
        raise InvalidPDFError("el archivo no es un PDF valido o esta dañado") from exc

    with document:
        if document.needs_pass:
            raise InvalidPDFError("el PDF esta protegido con contraseña")
        if output_format == OutputFormat.MARKDOWN:
            content = _to_markdown(document)
        else:
            content = "\n".join(page.get_text() for page in document)
        return content.strip(), document.page_count


def _to_markdown(document: pymupdf.Document) -> str:
    # sin tablas ni graficos vectoriales: son lo mas caro en cpu
    return pymupdf4llm.to_markdown(
        document,
        show_progress=False,
        ignore_images=True,
        ignore_graphics=True,
        table_strategy=None,
    )

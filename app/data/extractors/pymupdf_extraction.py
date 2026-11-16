"""extraccion con pymupdf; corre dentro de los procesos del pool, por eso son funciones sueltas"""

import pymupdf

from app.business.domain.exceptions import InvalidPDFError
from app.business.entities.extraction import OutputFormat
from app.data.extractors.markdown_writer import to_markdown

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
            content = to_markdown(document)
        else:
            content = "\n".join(page.get_text() for page in document)
        return content.strip(), document.page_count


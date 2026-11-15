"""lectura del pdf desde la request: multipart (campo file) o body binario"""

from fastapi import Request
from starlette.datastructures import UploadFile

from app.business.domain.exceptions import InvalidPDFError

FILE_FIELD = "file"


async def read_pdf_bytes(request: Request) -> bytes:
    content_type = request.headers.get("content-type", "")
    if not content_type.startswith("multipart/form-data"):
        return await request.body()

    async with request.form() as form:
        upload = form.get(FILE_FIELD)
        if not isinstance(upload, UploadFile):
            raise InvalidPDFError(f"falta el campo '{FILE_FIELD}' con el PDF")
        return await upload.read()

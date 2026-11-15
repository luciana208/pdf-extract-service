"""composicion: unico lugar que elige las implementaciones concretas"""

from fastapi import Request

from app.config.settings import settings
from app.presentation.controllers.extraction_controller import ExtractionController
from app.use_cases.extract_text import ExtractTextUseCase


def get_extraction_controller(request: Request) -> ExtractionController:
    # el extractor (y su pool de procesos) vive en app.state, se crea una vez en el lifespan
    extractor = request.app.state.extractor
    return ExtractionController(ExtractTextUseCase(extractor, settings.max_pdf_size_bytes))

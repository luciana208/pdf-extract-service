from dataclasses import dataclass
from enum import StrEnum


class OutputFormat(StrEnum):
    MARKDOWN = "markdown"
    TEXT = "text"


@dataclass(frozen=True)
class ExtractionResult:
    content: str
    page_count: int

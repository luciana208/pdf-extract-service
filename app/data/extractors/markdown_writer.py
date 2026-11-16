"""conversion liviana de pdf a markdown: titulos por tamaño de letra y un parrafo por bloque"""

from collections import Counter

import pymupdf

# recorta lo que queda fuera de la pagina; sin imagenes, que no aportan texto
_TEXT_FLAGS = pymupdf.TEXT_PRESERVE_WHITESPACE | pymupdf.TEXT_MEDIABOX_CLIP
_HEADING_LEVELS = 3


def to_markdown(document: pymupdf.Document) -> str:
    """
    lee cada pagina una sola vez con get_text("dict"). el tamaño de letra con mas texto es
    el del cuerpo y los tres tamaños mayores pasan a ser titulos #, ## y ###. cada bloque
    de texto es un parrafo. no detecta columnas, listas ni tablas: es lo que mas cpu cuesta.
    """
    paragraphs = [
        paragraph
        for page in document
        for paragraph in _paragraphs(page.get_text("dict", flags=_TEXT_FLAGS, sort=True)["blocks"])
    ]
    levels = _heading_levels(paragraphs)
    return "\n\n".join(f"{levels[size]} {text}" if size in levels else text for text, size in paragraphs)


def _paragraphs(blocks: list[dict]) -> list[tuple[str, int]]:
    # un parrafo por bloque, con el tamaño de letra de su primera linea
    result = []
    for block in blocks:
        lines = []
        for line in block.get("lines", ()):
            spans = line["spans"]
            text = "".join(span["text"] for span in spans).strip()
            if text:
                lines.append((text, round(max(span["size"] for span in spans))))
        if lines:
            result.append((" ".join(text for text, _ in lines), lines[0][1]))
    return result


def _heading_levels(paragraphs: list[tuple[str, int]]) -> dict[int, str]:
    weight = Counter()
    for text, size in paragraphs:
        weight[size] += len(text)
    if not weight:
        return {}
    body = weight.most_common(1)[0][0]
    bigger = sorted((size for size in weight if size > body), reverse=True)[:_HEADING_LEVELS]
    return {size: "#" * (level + 1) for level, size in enumerate(bigger)}

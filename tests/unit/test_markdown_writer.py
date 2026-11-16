import pymupdf

from app.data.extractors.markdown_writer import to_markdown
from tests.pdf_factory import build_pdf, build_pdf_with_title


def _open(data: bytes) -> pymupdf.Document:
    return pymupdf.open(stream=data, filetype="pdf")


def test_titulo_en_letra_grande_sale_con_numeral():
    content = to_markdown(_open(build_pdf_with_title("Informe anual", "texto del cuerpo")))
    assert content.startswith("# Informe anual")


def test_cuerpo_sale_como_parrafo_sin_numeral():
    content = to_markdown(_open(build_pdf_with_title("Informe anual", "texto del cuerpo")))
    assert "texto del cuerpo" in content.splitlines()


def test_titulo_y_cuerpo_separados_por_linea_en_blanco():
    content = to_markdown(_open(build_pdf_with_title("Informe anual", "texto del cuerpo")))
    assert content == "# Informe anual\n\ntexto del cuerpo"


def test_texto_de_un_solo_tamaño_no_lleva_titulos():
    content = to_markdown(_open(build_pdf(["Hola Mundo PDF", "Segunda pagina"])))
    assert "#" not in content
    assert "Hola Mundo PDF" in content
    assert "Segunda pagina" in content


def test_pdf_sin_texto_devuelve_vacio():
    assert to_markdown(_open(build_pdf([""]))) == ""

"""Catálogo A4 en memoria. Las dos variantes comparten datos y paginación."""

from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

import reportlab
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Flowable,
    HRFlowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from .templatetags.catalog_format import ars


def _styles():
    # Fuentes Unicode incluidas en ReportLab; no hay descarga ni dependencia de fuentes del SO.
    fonts = Path(reportlab.__file__).parent / "fonts"
    if "CatalogSans" not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont("CatalogSans", str(fonts / "Vera.ttf")))
        pdfmetrics.registerFont(TTFont("CatalogSansBold", str(fonts / "VeraBd.ttf")))
        pdfmetrics.registerFontFamily("CatalogSans", normal="CatalogSans", bold="CatalogSansBold")
    body = ParagraphStyle("body", fontName="CatalogSans", fontSize=9, leading=12,
                          textColor=colors.HexColor("#292324"), spaceAfter=3)
    return body, ParagraphStyle("name", parent=body, fontName="CatalogSansBold", fontSize=11, leading=14), ParagraphStyle(
        "photo-label", parent=body, fontSize=7, leading=10, textColor=colors.HexColor("#655c58"),
    )


def _paragraph(value, style):
    text = escape(str(value)).replace("\r\n", "\n").replace("\r", "\n").replace("\n", "<br/>")
    return Paragraph(text, style)


def _product_text(product, body, name):
    fields = [
        _paragraph(product.name, name),
        _paragraph(f"Categoría: {product.category.name}", body),
    ]
    if product.brand:
        fields.append(_paragraph(f"Marca: {product.brand}", body))
    if product.description:
        fields.append(_paragraph(product.description, body))
    fields.extend([
        _paragraph(f"Unidad de venta: {product.get_sale_unit_display()}", body),
        _paragraph(f"Precio minorista: {ars(product.retail_price)}", body),
    ])
    if product.wholesale_price is not None:
        fields.append(_paragraph(f"Precio mayorista: {ars(product.wholesale_price)}", body))
    if product.wholesale_condition:
        fields.append(_paragraph(f"Condición mayorista: {product.wholesale_condition}", body))
    if not product.is_active:
        fields.append(_paragraph("Estado: Inactivo", body))
    return fields


class _Photo(Flowable):
    def __init__(self, buffer, width, height):
        super().__init__()
        self.image = PILImage.open(buffer)
        self.width, self.height = width, height

    def draw(self):
        # La caché drawImage identifica píxeles sin dimensiones: una foto uniforme
        # horizontal/vertical puede colisionar. Inline conserva cada JPEG y proporción.
        self.canv.drawInlineImage(self.image, 0, 0, width=self.width, height=self.height)


def _photo(product, label_style):
    if not product.image:
        return _paragraph("Sin imagen", label_style)
    try:
        with product.image.open("rb") as stored, PILImage.open(stored) as original:
            # Copia temporal reducida: jamás guarda ni reoptimiza el archivo comercial.
            original.thumbnail((240, 240))
            rgba = original.convert("RGBA")
            reduced = PILImage.new("RGB", rgba.size, "white")
            reduced.paste(rgba, mask=rgba.getchannel("A"))
            buffer = BytesIO()
            reduced.save(buffer, format="JPEG", quality=82)
            buffer.seek(0)
            width, height = reduced.size
        scale = 56 / max(width, height)  # 56 pt ≈ 75 px; contain en ambas proporciones.
        return _Photo(buffer, width=width * scale, height=height * scale)
    except (OSError, ValueError, PILImage.DecompressionBombError):
        return _paragraph("Foto no disponible", label_style)


def build_catalog_pdf(products, *, include_images):
    body, name, label = _styles()
    output = BytesIO()
    document = SimpleDocTemplate(output, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
                                topMargin=29 * mm, bottomMargin=22 * mm)
    story = []
    for product in products:
        fields = _product_text(product, body, name)
        width = document.width - 12  # Padding del marco Platypus, 6 pt por lado.
        cells = [[_photo(product, label), fields]] if include_images else [[fields]]
        columns = [66, width - 66] if include_images else [width]
        row = Table(cells, colWidths=columns, splitByRow=0, splitInRow=1, hAlign="LEFT")
        commands = [
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]
        if include_images:
            commands.append(("RIGHTPADDING", (0, 0), (0, -1), 10))
        row.setStyle(TableStyle(commands))
        # Conserva registros normales juntos; uno mayor que la hoja se divide
        # en el espacio disponible sin dejar una página casi vacía por anticipado.
        story.append(KeepTogether([
            row, Spacer(1, 6),
            HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#c9c3bf")), Spacer(1, 10),
        ], maxHeight=document.height - 12))
    if not story:
        story.append(_paragraph("No hay productos para los filtros seleccionados", body))

    def page_frame(canvas, doc):
        canvas.saveState()
        canvas.setTitle("Dulce y Salado — Catálogo de productos")
        canvas.setAuthor("Dulce y Salado")
        canvas.setFillColor(colors.HexColor("#292324"))
        canvas.setFont("CatalogSansBold", 13)
        canvas.drawString(doc.leftMargin, A4[1] - 16 * mm, "Dulce y Salado")
        canvas.setFont("CatalogSans", 9)
        canvas.drawString(doc.leftMargin, A4[1] - 22 * mm, "Catálogo de productos")
        canvas.setFont("CatalogSans", 7)
        canvas.drawString(doc.leftMargin, 14 * mm, "Precios estimativos en ARS. Disponibilidad y condiciones a confirmar con el comercio.")
        canvas.drawRightString(A4[0] - doc.rightMargin, 9 * mm, f"Página {doc.page}")
        canvas.restoreState()

    document.build(story, onFirstPage=page_frame, onLaterPages=page_frame)
    return output.getvalue()

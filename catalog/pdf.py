"""Catálogo A4 en memoria. Las dos variantes comparten datos y paginación."""

from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

import reportlab
from django.contrib.staticfiles import finders
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
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


def _escaped_text(value):
    return escape(str(value)).replace("\r\n", "\n").replace("\r", "\n").replace("\n", "<br/>")


def _paragraph(value, style):
    return Paragraph(_escaped_text(value), style)


def _labelled(label, value, style):
    return Paragraph(f"<b>{escape(label)}:</b> {_escaped_text(value)}", style)


def _product_text(product, body, name):
    fields = [
        _paragraph(product.name, name),
        _labelled("Categoría", product.category.name, body),
    ]
    if product.brand:
        fields.append(_labelled("Marca", product.brand, body))
    if product.description:
        fields.append(_paragraph(product.description, body))
    fields.extend([
        _labelled("Unidad de venta", product.get_sale_unit_display(), body),
        _labelled("Precio minorista", ars(product.retail_price), body),
    ])
    if product.wholesale_price is not None:
        fields.append(_labelled("Precio mayorista", ars(product.wholesale_price), body))
    if product.wholesale_condition:
        fields.append(_labelled("Condición mayorista", product.wholesale_condition, body))
    if not product.is_active:
        fields.append(_labelled("Estado", "Inactivo", body))
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


def _photo(product, label_style, *, max_side=56):
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
        scale = max_side / max(width, height)  # Contain, sin recortar ni modificar el original.
        return _Photo(buffer, width=width * scale, height=height * scale)
    except (OSError, ValueError, PILImage.DecompressionBombError):
        return _paragraph("Foto no disponible", label_style)


def _page_frame(canvas, doc):
    width, height = doc.pagesize
    canvas.saveState()
    canvas.setTitle("Dulce y Salado — Catálogo de productos")
    canvas.setAuthor("Dulce y Salado")
    canvas.setFillColor(colors.HexColor("#292324"))
    text_left = doc.leftMargin
    try:
        logo_path = finders.find("img/logo.webp")
        if logo_path:
            logo = ImageReader(logo_path)
            logo_width, logo_height = logo.getSize()
            size = 16 * mm
            scale = min(size / logo_width, size / logo_height)
            canvas.drawImage(logo, doc.leftMargin, height - 24 * mm + (size - logo_height * scale) / 2,
                             width=logo_width * scale, height=logo_height * scale, mask="auto")
            text_left += size + 4 * mm
    except (OSError, ValueError):
        # El encabezado textual permanece disponible si el recurso falta/no se puede leer.
        pass
    canvas.setFont("CatalogSansBold", 13)
    canvas.drawString(text_left, height - 16 * mm, "Dulce y Salado")
    canvas.setFont("CatalogSans", 9)
    canvas.drawString(text_left, height - 22 * mm, "Catálogo de productos")
    canvas.setFont("CatalogSans", 7)
    canvas.drawString(doc.leftMargin, 14 * mm, "Precios estimativos en ARS. Disponibilidad y condiciones a confirmar con el comercio.")
    canvas.drawRightString(width - doc.rightMargin, 9 * mm, f"Página {doc.page}")
    canvas.restoreState()


class _ImageListRow(Table):
    def split(self, availWidth, availHeight):
        # ReportLab acumula padding al dividir una celda MIDDLE: una fila muy
        # extensa puede dejar de avanzar. Dividir en TOP y centrar cada fragmento.
        self.setStyle(TableStyle([("VALIGN", (0, 0), (0, -1), "TOP")]))
        try:
            parts = super().split(availWidth, availHeight)
        finally:
            self.setStyle(TableStyle([("VALIGN", (0, 0), (0, -1), "MIDDLE")]))
        for part in parts:
            part.setStyle(TableStyle([("VALIGN", (0, 0), (0, -1), "MIDDLE")]))
        return parts


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
        row_type = _ImageListRow if include_images else Table
        row = row_type(cells, colWidths=columns, splitByRow=0, splitInRow=1, hAlign="LEFT")
        commands = [
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]
        if include_images:
            commands.append(("RIGHTPADDING", (0, 0), (0, -1), 10))
            commands.append(("VALIGN", (0, 0), (0, -1), "MIDDLE"))
        row.setStyle(TableStyle(commands))
        # Conserva registros normales juntos; uno mayor que la hoja se divide
        # en el espacio disponible sin dejar una página casi vacía por anticipado.
        story.append(KeepTogether([
            row, Spacer(1, 6),
            HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#c9c3bf")), Spacer(1, 10),
        ], maxHeight=document.height - 12))
    if not story:
        story.append(_paragraph("No hay productos para los filtros seleccionados", body))

    document.build(story, onFirstPage=_page_frame, onLaterPages=_page_frame)
    return output.getvalue()


def build_catalog_table_pdf(products, *, include_images=False):
    body, _, label = _styles()
    cell = ParagraphStyle("table-cell", parent=body, fontSize=9, leading=12, spaceAfter=0)
    header = ParagraphStyle("table-header", parent=cell, fontName="CatalogSansBold")
    output = BytesIO()
    document = SimpleDocTemplate(output, pagesize=landscape(A4), leftMargin=16 * mm, rightMargin=16 * mm,
                                topMargin=29 * mm, bottomMargin=22 * mm)
    headings = ("Imagen", "Producto", "Marca", "Descripción", "Unidad de venta", "Precio minorista",
                "Precio mayorista", "Condición mayorista") if include_images else (
                    "Producto", "Marca", "Descripción", "Unidad", "$ Min.", "$ May.", "Cond. mayorista")
    rows = [[_paragraph(value, header) for value in headings]]
    for product in products:
        name = [_paragraph(product.name, cell)]
        if not product.is_active:
            name.append(_paragraph("Estado: Inactivo", cell))
        values = (product.brand, product.description, product.get_sale_unit_display(), ars(product.retail_price),
                  ars(product.wholesale_price) if product.wholesale_price is not None else "",
                  product.wholesale_condition)
        row = [name, *[_paragraph(value, cell) for value in values]]
        if include_images:
            row.insert(0, _photo(product, label, max_side=38))  # 38 pt ≈ 51 px.
        rows.append(row)
    story = []
    if len(rows) > 1:
        width = document.width - 12
        columns = ([48, *[(width - 48) * fraction for fraction in (.19, .10, .235, .085, .115, .115, .16)]]
                   if include_images else [width * fraction for fraction in (.20, .12, .26, .07, .105, .105, .14)])
        table = Table(rows, colWidths=columns, repeatRows=1, splitByRow=1, splitInRow=1, hAlign="LEFT")
        table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LINEBELOW", (0, 0), (-1, 0), .7, colors.HexColor("#655c58")),
            ("LINEBELOW", (0, 1), (-1, -1), .4, colors.HexColor("#c9c3bf")),
        ]))
        story.append(table)
    else:
        story.append(_paragraph("No hay productos para los filtros seleccionados", body))
    document.build(story, onFirstPage=_page_frame, onLaterPages=_page_frame)
    return output.getvalue()

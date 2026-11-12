
from io import BytesIO

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader

from apps.catalog.barcodes import (
    generate_code128,
    generate_qr,
    ensure_product_barcode,
)


def generate_label_pdf(products, output_path):

    page_width, page_height = A4

    # A4 sticker sheet configuration.
    columns = 3
    rows = 8

    label_width = 63.5 * mm
    label_height = 33.9 * mm

    total_width = columns * label_width
    total_height = rows * label_height

    margin_x = (page_width - total_width) / 2
    margin_y = (page_height - total_height) / 2

    pdf = canvas.Canvas(
        output_path,
        pagesize=A4
    )

    products = list(products)

    for index, product in enumerate(products):

        if index > 0 and index % (columns * rows) == 0:
            pdf.showPage()

        barcode_record = ensure_product_barcode(product)
        identifier = barcode_record.barcode_value

        barcode_image = ImageReader(
            BytesIO(generate_code128(identifier))
        )

        qr_image = ImageReader(
            BytesIO(generate_qr(identifier))
        )

        position = index % (columns * rows)

        column = position % columns
        row = position // columns

        x = margin_x + column * label_width

        y = (
            page_height
            - margin_y
            - (row + 1) * label_height
        )

        # Product name.
        pdf.setFont("Helvetica-Bold", 8)
        pdf.drawString(
            x + 2 * mm,
            y + 27 * mm,
            product.name[:35]
        )

        # SKU.
        pdf.setFont("Helvetica", 6)
        pdf.drawString(
            x + 2 * mm,
            y + 23 * mm,
            f"SKU: {product.sku[:25]}"
        )

        # QR code.
        pdf.drawImage(
            qr_image,
            x + 2 * mm,
            y + 3 * mm,
            width=17 * mm,
            height=17 * mm,
            preserveAspectRatio=True
        )

        # Code 128 barcode.
        pdf.drawImage(
            barcode_image,
            x + 20 * mm,
            y + 5 * mm,
            width=41 * mm,
            height=16 * mm,
            preserveAspectRatio=True,
            anchor="c",
            mask="auto"
        )

    pdf.save()

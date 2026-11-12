
import uuid
from io import BytesIO

import barcode
import qrcode

from barcode.writer import ImageWriter

from django.db import transaction

from apps.catalog.models import ProductBarcode


def ensure_product_barcode(product):
    """
    Return the primary barcode for a product.
    Generate an internal identifier if none exists.
    """

    existing = ProductBarcode.objects.filter(
        product=product,
        is_primary=True
    ).first()

    if existing:
        return existing

    # Reuse an existing manufacturer barcode if available.
    existing = ProductBarcode.objects.filter(
        product=product
    ).order_by("created_at").first()

    if existing:
        existing.is_primary = True
        existing.save(update_fields=["is_primary"])
        return existing

    # Generate a unique internal identifier.
    while True:
        value = f"S99-{uuid.uuid4().hex[:16].upper()}"

        if not ProductBarcode.objects.filter(
            tenant=product.tenant,
            barcode_value=value
        ).exists():
            break

    return ProductBarcode.objects.create(
        tenant=product.tenant,
        product=product,
        barcode_value=value,
        barcode_type=ProductBarcode.BarcodeType.CODE128,
        is_primary=True,
    )


def generate_code128(value):
    """Return Code 128 barcode as PNG bytes."""

    barcode_class = barcode.get_barcode_class("code128")

    barcode_instance = barcode_class(
        value,
        writer=ImageWriter()
    )

    buffer = BytesIO()

    barcode_instance.write(
        buffer,
        options={
            "module_width": 0.20,
            "module_height": 12,
            "font_size": 8,
            "text_distance": 4,
            "quiet_zone": 2,
        }
    )

    return buffer.getvalue()


def generate_qr(value):
    """Return QR code as PNG bytes."""

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=3,
    )

    qr.add_data(value)
    qr.make(fit=True)

    image = qr.make_image(
        fill_color="black",
        back_color="white"
    )

    buffer = BytesIO()
    image.save(buffer, format="PNG")

    return buffer.getvalue()


@transaction.atomic
def generate_product_codes(product):
    """
    Ensure a primary product identifier exists
    and generate both visual representations.
    """

    # Lock product to avoid concurrent barcode creation.
    from apps.catalog.models import Product

    product = Product.objects.select_for_update().get(
        pk=product.pk,
        tenant=product.tenant
    )

    product_barcode = ensure_product_barcode(product)

    return {
        "product": product,
        "identifier": product_barcode.barcode_value,
        "barcode_png": generate_code128(
            product_barcode.barcode_value
        ),
        "qr_png": generate_qr(
            product_barcode.barcode_value
        ),
    }

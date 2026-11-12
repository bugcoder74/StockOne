
from pathlib import Path

from django.core.management.base import (
    BaseCommand,
    CommandError,
)

from apps.tenants.models import Tenant
from apps.catalog.models import Product
from apps.catalog.label_generator import generate_label_pdf


class Command(BaseCommand):

    help = "Export printable barcode and QR labels for a tenant."

    def add_arguments(self, parser):
        parser.add_argument(
            "--tenant",
            required=True,
            help="Tenant slug"
        )

        parser.add_argument(
            "--output",
            default="shop99_barcode_labels.pdf",
            help="Output PDF path"
        )

    def handle(self, *args, **options):

        slug = options["tenant"]

        try:
            tenant = Tenant.objects.get(
                slug=slug,
                is_active=True
            )
        except Tenant.DoesNotExist:
            raise CommandError("Tenant not found.")

        products = Product.objects.filter(
            tenant=tenant,
            is_active=True
        ).order_by("name").prefetch_related("barcodes")

        if not products.exists():
            raise CommandError(
                "No active products found."
            )

        output_path = Path(options["output"])
        output_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        generate_label_pdf(
            products,
            str(output_path)
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Labels generated: {output_path.resolve()}"
            )
        )

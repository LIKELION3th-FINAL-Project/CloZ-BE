import csv

from django.core.management.base import BaseCommand
from pathlib import PureWindowsPath
from product.models import Product
from django.db import transaction

class Command(BaseCommand):
    help = "Import products from CSV"

    def add_arguments(self, parser):
        parser.add_argument(
            "--csv",
            type=str,
            required=True,
            help="CSV file path"
        )

    @transaction.atomic
    def handle(self, *args, **options):
        csv_path = options["csv"]

        products = []

        with open(csv_path, newline="", encoding="utf-8-sig") as csvfile:
            reader = csv.DictReader(csvfile)

            for row in reader:
                # 이미지 경로 전처리 (절대경로 제거)
                raw_path = row["product_image_path"]
                win_path = PureWindowsPath(raw_path)
                parts = win_path.parts

                idx = parts.index("musinsa_images")
                relative_path = "/".join(parts[idx:])

                image_path = relative_path

                products.append(
                    Product(
                        product_name=row["product_name"],
                        brand=row["brand"],
                        category_main=row["category_main"],
                        category_sub=row["category_sub"],
                        product_url=row["product_url"],
                        price=row["price"],
                        product_image_path=image_path,
                    )
                )

        Product.objects.bulk_create(products, batch_size=1000)

        self.stdout.write(
            self.style.SUCCESS(f"Imported {len(products)} products")
        )

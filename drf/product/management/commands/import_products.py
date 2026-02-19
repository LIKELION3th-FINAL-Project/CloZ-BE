import csv
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from product.models import Product


class Command(BaseCommand):
    help = "Import products from CSV (havati dataset)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--csv",
            type=str,
            required=True,
            help="CSV file path (e.g. data/products.csv)"
        )
        parser.add_argument(
            "--image-root",
            type=str,
            default="havati_products",
            help="Image root directory name inside data/"
        )

    @transaction.atomic
    def handle(self, *args, **options):
        csv_path = Path(options["csv"])
        image_root = options["image_root"]

        products = []

        with csv_path.open(newline="", encoding="utf-8-sig") as csvfile:
            reader = csv.DictReader(csvfile)

            for row in reader:
                # price: "548,000" -> 548000
                price = int(row["price"].replace(",", ""))

                # image_file 예: havati_products/OUTER/Jacket_Blouson/xxx.jpg
                image_path = row["image_file"]

                # 혹시 image_file에 앞 경로가 더 붙어와도 대비
                if image_root in image_path:
                    image_path = image_path.split(image_root, 1)[1].lstrip("/")
                    image_path = f"{image_root}/{image_path}"

                products.append(
                    Product(
                        product_name=row["name"],
                        brand=row["brand"],
                        category_main=row["main_category"],
                        category_sub=row["sub_category"],
                        product_url=row["url"],
                        price=price,
                        product_image_path=image_path,
                    )
                )

        Product.objects.bulk_create(products, batch_size=1000)

        self.stdout.write(
            self.style.SUCCESS(f"Imported {len(products)} products")
        )

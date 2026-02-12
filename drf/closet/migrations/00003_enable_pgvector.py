from django.db import migrations
from pgvector.django import VectorExtension

class Migration(migrations.Migration):
    dependencies = [
        ("closet", "0002_remove_closet_image_url_closet_image"),
    ]

    operations = [
        VectorExtension(),
    ]
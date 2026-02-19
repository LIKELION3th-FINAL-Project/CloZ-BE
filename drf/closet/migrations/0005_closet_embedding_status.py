from django.db import migrations, models


def backfill_embedding_status(apps, schema_editor):
    Closet = apps.get_model("closet", "Closet")
    Closet.objects.filter(embedding__isnull=False).update(
        embedding_status="DONE"
    )


class Migration(migrations.Migration):
    dependencies = [
        ("closet", "0004_closet_embedding_closet_style_cat"),
    ]

    operations = [
        migrations.AddField(
            model_name="closet",
            name="embedding_status",
            field=models.CharField(
                choices=[
                    ("PENDING", "대기"),
                    ("PROCESSING", "처리중"),
                    ("DONE", "완료"),
                    ("FAILED", "실패"),
                ],
                default="PENDING",
                max_length=20,
            ),
        ),
        migrations.RunPython(
            code=backfill_embedding_status,
            reverse_code=migrations.RunPython.noop,
        ),
    ]

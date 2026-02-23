from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("user", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="body_image",
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to="body_images/",
            ),
        ),
    ]

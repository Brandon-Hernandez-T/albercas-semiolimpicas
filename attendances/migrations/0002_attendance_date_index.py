from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("attendances", "0001_initial"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="attendance",
            index=models.Index(
                fields=["attendance_date"],
                name="attendances_date_idx",
            ),
        ),
    ]

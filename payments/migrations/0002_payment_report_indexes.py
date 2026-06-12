from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("payments", "0001_initial"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="payment",
            index=models.Index(
                fields=["client", "expiration_date"],
                name="payments_client_expiration",
            ),
        ),
        migrations.AddIndex(
            model_name="payment",
            index=models.Index(
                fields=["expiration_date"],
                name="payments_expiration_date_idx",
            ),
        ),
    ]

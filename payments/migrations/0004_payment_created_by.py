# Generated manually for Payment.created_by

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("payments", "0003_alter_payment_status"),
    ]

    operations = [
        migrations.AddField(
            model_name="payment",
            name="created_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="payments_registered",
                to=settings.AUTH_USER_MODEL,
                verbose_name="registrado por",
            ),
        ),
    ]

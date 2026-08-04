# Add Client.pool (nullable → assign default → required)

import django.db.models.deletion
from django.db import migrations, models


DEFAULT_POOL_CODE = "ixtapaluca"


def assign_default_pool(apps, schema_editor):
    Client = apps.get_model("clients", "Client")
    Pool = apps.get_model("venues", "Pool")
    pool = Pool.objects.get(code=DEFAULT_POOL_CODE)
    Client.objects.filter(pool__isnull=True).update(pool=pool)


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("clients", "0004_client_emergency_phone"),
        ("venues", "0002_seed_default_pool"),
    ]

    operations = [
        migrations.AddField(
            model_name="client",
            name="pool",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="clients",
                to="venues.pool",
                verbose_name="alberca",
            ),
        ),
        migrations.RunPython(assign_default_pool, noop_reverse),
        migrations.AlterField(
            model_name="client",
            name="pool",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="clients",
                to="venues.pool",
                verbose_name="alberca",
            ),
        ),
    ]

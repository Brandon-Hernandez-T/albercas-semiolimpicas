# Seed default pool for existing clients

from django.db import migrations


DEFAULT_POOL_CODE = "ixtapaluca"
DEFAULT_POOL_NAME = "Ixtapaluca"


def seed_default_pool(apps, schema_editor):
    Pool = apps.get_model("venues", "Pool")
    Pool.objects.get_or_create(
        code=DEFAULT_POOL_CODE,
        defaults={"name": DEFAULT_POOL_NAME, "active": True},
    )


def unseed_default_pool(apps, schema_editor):
    Pool = apps.get_model("venues", "Pool")
    Pool.objects.filter(code=DEFAULT_POOL_CODE).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("venues", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_default_pool, unseed_default_pool),
    ]

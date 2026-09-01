from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("clients", "0005_client_pool"),
        ("memberships", "0007_membershipplan_billing_mode"),
    ]

    operations = [
        migrations.AddField(
            model_name="client",
            name="is_walk_in",
            field=models.BooleanField(
                default=False,
                help_text="Cliente sistema para registrar visitas sin datos del nadador. No aparece en el catálogo de socios.",
                verbose_name="cliente de visitas ocasionales",
            ),
        ),
    ]

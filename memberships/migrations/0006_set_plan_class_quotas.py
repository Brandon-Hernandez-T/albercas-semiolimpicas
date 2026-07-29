from django.db import migrations


def set_plan_quotas(apps, schema_editor):
    MembershipPlan = apps.get_model("memberships", "MembershipPlan")
    quotas = {
        "entre-semana": {"class_quota": 15, "max_visits_per_day": 2},
        "completo": {"class_quota": 20, "max_visits_per_day": 2},
        "fin-de-semana": {"class_quota": 8, "max_visits_per_day": 2},
    }
    for slug, values in quotas.items():
        MembershipPlan.objects.filter(slug=slug).update(**values)


def clear_plan_quotas(apps, schema_editor):
    MembershipPlan = apps.get_model("memberships", "MembershipPlan")
    MembershipPlan.objects.filter(
        slug__in=["entre-semana", "completo", "fin-de-semana"]
    ).update(class_quota=None, max_visits_per_day=None)


class Migration(migrations.Migration):

    dependencies = [
        ("memberships", "0005_class_quota_and_multi_attendance"),
    ]

    operations = [
        migrations.RunPython(set_plan_quotas, clear_plan_quotas),
    ]

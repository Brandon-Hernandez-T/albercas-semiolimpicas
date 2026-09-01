from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin

from .constants import format_allowed_days, format_class_quota
from .forms import MembershipPlanAdminForm
from .models import MembershipPlan


@admin.register(MembershipPlan)
class MembershipPlanAdmin(ModelAdmin):
    form = MembershipPlanAdminForm
    list_display = (
        "name",
        "slug",
        "display_allowed_days",
        "display_class_quota",
        "price",
        "billing_mode",
        "duration_days",
        "is_active",
        "updated_at",
    )
    list_filter = ("is_active",)
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("created_at", "updated_at")

    @admin.display(description=_("días permitidos"))
    def display_allowed_days(self, obj):
        return format_allowed_days(obj.allowed_days)

    @admin.display(description=_("cupo de clases"))
    def display_class_quota(self, obj):
        return format_class_quota(obj.class_quota, obj.max_visits_per_day)

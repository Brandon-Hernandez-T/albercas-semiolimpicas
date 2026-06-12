from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import MembershipPlan


@admin.register(MembershipPlan)
class MembershipPlanAdmin(ModelAdmin):
    list_display = ("name", "slug", "price", "duration_days", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("created_at", "updated_at")

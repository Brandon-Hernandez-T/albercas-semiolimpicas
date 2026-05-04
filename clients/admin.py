from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import Client


@admin.register(Client)
class ClientAdmin(ModelAdmin):
    list_display = (
        "name",
        "access_number",
        "membership_plan",
        "active",
        "updated_at",
    )
    list_filter = ("active", "membership_plan")
    search_fields = ("name", "access_number")
    autocomplete_fields = ("membership_plan",)

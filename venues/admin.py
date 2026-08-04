from django.contrib import admin
from unfold.admin import ModelAdmin, StackedInline

from .models import Pool, StaffProfile


class StaffProfileInline(StackedInline):
    model = StaffProfile
    extra = 0
    max_num = 1
    autocomplete_fields = ("pool",)
    verbose_name = "Perfil / alberca"
    verbose_name_plural = "Perfil / alberca"


@admin.register(Pool)
class PoolAdmin(ModelAdmin):
    list_display = ("name", "code", "active", "updated_at")
    list_filter = ("active",)
    search_fields = ("name", "code")
    prepopulated_fields = {"code": ("name",)}
    readonly_fields = ("created_at", "updated_at")

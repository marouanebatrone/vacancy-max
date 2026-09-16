from typing import TYPE_CHECKING

from django.contrib import admin

from .models import Holiday

if TYPE_CHECKING:
    # django-stubs makes ModelAdmin generic, but it is not subscriptable at
    # runtime. This keeps mypy --strict happy without breaking the import.
    HolidayAdminBase = admin.ModelAdmin[Holiday]
else:
    HolidayAdminBase = admin.ModelAdmin


@admin.register(Holiday)
class HolidayAdmin(HolidayAdminBase):
    list_display = ["date", "name", "kind", "is_confirmed", "uncertainty_days"]
    list_filter = ["year", "kind", "is_confirmed"]
    search_fields = ["name", "name_fr", "name_ar", "slug"]
    ordering = ["-year", "date"]

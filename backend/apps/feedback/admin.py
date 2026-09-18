from typing import TYPE_CHECKING

from django.contrib import admin

from .models import Feedback

if TYPE_CHECKING:
    FeedbackAdminBase = admin.ModelAdmin[Feedback]
else:
    FeedbackAdminBase = admin.ModelAdmin


@admin.register(Feedback)
class FeedbackAdmin(FeedbackAdminBase):
    list_display = ["created_at", "__str__", "thumbs_up", "thumbs_down"]
    list_filter = ["thumbs_up", "created_at"]
    search_fields = ["comment"]
    readonly_fields = ["id", "created_at"]
    date_hierarchy = "created_at"

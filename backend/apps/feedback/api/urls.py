from django.urls import URLPattern, URLResolver, path

from .views import FeedbackView

app_name = "feedback"

urlpatterns: list[URLPattern | URLResolver] = [
    path("", FeedbackView.as_view(), name="feedback"),
]

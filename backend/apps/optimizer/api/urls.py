from django.urls import URLPattern, URLResolver, path

from .views import PlanCalendarView, PlanView

app_name = "optimizer"

urlpatterns: list[URLPattern | URLResolver] = [
    path("plan/", PlanView.as_view(), name="plan"),
    path("plan.ics", PlanCalendarView.as_view(), name="plan-ics"),
]

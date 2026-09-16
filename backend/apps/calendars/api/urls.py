from django.urls import URLPattern, URLResolver, path

from .views import SupportedYearsView, YearOverviewView

app_name = "calendars"

urlpatterns: list[URLPattern | URLResolver] = [
    path("years/", SupportedYearsView.as_view(), name="supported-years"),
    path("years/<int:year>/", YearOverviewView.as_view(), name="year-overview"),
]

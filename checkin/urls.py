from django.urls import path

from . import views

app_name = "checkin"

urlpatterns = [
    path("", views.quick_checkin, name="quick_checkin"),
    path("suggestions/", views.client_suggestions, name="client_suggestions"),
    path("lookup/", views.client_lookup, name="client_lookup"),
]

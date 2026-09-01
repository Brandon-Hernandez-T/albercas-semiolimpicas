from django.urls import path

from . import views

app_name = "checkin"

urlpatterns = [
    path("", views.quick_checkin, name="quick_checkin"),
    path("registrar-visita/", views.register_visit, name="register_visit"),
    path("suggestions/", views.client_suggestions, name="client_suggestions"),
    path("lookup/", views.client_lookup, name="client_lookup"),
]

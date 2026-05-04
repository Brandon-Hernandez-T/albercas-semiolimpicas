from django.urls import path

from . import views

app_name = "checkin"

urlpatterns = [
    path("", views.quick_checkin, name="quick_checkin"),
]

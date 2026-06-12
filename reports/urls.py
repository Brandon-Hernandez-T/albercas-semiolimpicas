from django.urls import path

from . import views

app_name = "reports"

urlpatterns = [
    path("", views.index, name="index"),
    path("asistencias/", views.attendance_report_view, name="attendances"),
    path("asistencias.csv", views.attendance_report_csv_view, name="attendances_csv"),
    path("ingresos/", views.revenue_report_view, name="revenue"),
    path("ingresos.csv", views.revenue_report_csv_view, name="revenue_csv"),
    path("por-vencer/", views.expiring_report_view, name="expiring"),
    path("por-vencer.csv", views.expiring_report_csv_view, name="expiring_csv"),
]

from functools import wraps

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, render
from django.urls import reverse

from .csv_export import attendances_csv, expiring_csv, payments_csv
from .forms import DateRangeForm, ExpiringDaysForm
from .services import (
    attendance_report,
    default_month_range,
    expiring_memberships,
    revenue_report,
)


def staff_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
            return HttpResponseForbidden(
                "<!DOCTYPE html><html lang='es'><meta charset='utf-8'>"
                "<body><p>Solo personal staff.</p></body></html>",
                content_type="text/html; charset=utf-8",
            )
        return view_func(request, *args, **kwargs)

    return wrapper


@staff_required
def index(request):
    return render(request, "reports/index.html")


def _parse_date_range(request):
    form = DateRangeForm(request.GET or None)
    if request.GET and form.is_valid():
        return form, form.resolved_range()
    start, end = default_month_range()
    if not request.GET:
        form = DateRangeForm(initial={"date_from": start, "date_to": end})
    return form, (start, end)


@staff_required
def attendance_report_view(request):
    form, date_range = _parse_date_range(request)
    report = attendance_report(*date_range) if date_range else None
    return render(
        request,
        "reports/attendances.html",
        {
            "form": form,
            "report": report,
            "csv_url": reverse("reports:attendances_csv"),
        },
    )


@staff_required
def attendance_report_csv_view(request):
    form = DateRangeForm(request.GET or None)
    if not form.is_valid():
        return redirect("reports:attendances")
    return attendances_csv(*form.resolved_range())


@staff_required
def revenue_report_view(request):
    form, date_range = _parse_date_range(request)
    report = revenue_report(*date_range) if date_range else None
    return render(
        request,
        "reports/revenue.html",
        {
            "form": form,
            "report": report,
            "csv_url": reverse("reports:revenue_csv"),
        },
    )


@staff_required
def revenue_report_csv_view(request):
    form = DateRangeForm(request.GET or None)
    if not form.is_valid():
        return redirect("reports:revenue")
    return payments_csv(*form.resolved_range())


@staff_required
def expiring_report_view(request):
    form = ExpiringDaysForm(request.GET or None)
    within_days = 30
    if request.GET and form.is_valid():
        within_days = form.cleaned_data["within_days"]
    rows = expiring_memberships(within_days)
    return render(
        request,
        "reports/expiring.html",
        {
            "form": form,
            "rows": rows,
            "within_days": within_days,
            "csv_url": reverse("reports:expiring_csv"),
        },
    )


@staff_required
def expiring_report_csv_view(request):
    form = ExpiringDaysForm(request.GET or None)
    if not form.is_valid():
        return redirect("reports:expiring")
    return expiring_csv(form.cleaned_data["within_days"])

from functools import wraps

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, render
from django.urls import reverse

from core.unfold_permissions import user_can_operate
from venues.scoping import user_pool, user_sees_all_pools

from .csv_export import attendances_csv, expiring_csv, payments_csv
from .forms import ExpiringDaysForm, PoolScopedDateRangeForm, RevenueFilterForm
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
        if not user_can_operate(request.user):
            return HttpResponseForbidden(
                "<!DOCTYPE html><html lang='es'><meta charset='utf-8'>"
                "<body><p>Solo personal staff.</p></body></html>",
                content_type="text/html; charset=utf-8",
            )
        return view_func(request, *args, **kwargs)

    return wrapper


def _default_pool_for_user(user):
    if user_sees_all_pools(user):
        return None
    return user_pool(user)


@staff_required
def index(request):
    return render(request, "reports/index.html")


@staff_required
def attendance_report_view(request):
    form = PoolScopedDateRangeForm(request.GET or None, user=request.user)
    report = None
    if request.GET:
        if form.is_valid():
            report = attendance_report(
                *form.resolved_range(),
                pool=form.resolved_pool(),
            )
    else:
        start, end = default_month_range()
        form = PoolScopedDateRangeForm(
            initial={"date_from": start, "date_to": end},
            user=request.user,
        )
        report = attendance_report(
            start, end, pool=_default_pool_for_user(request.user)
        )
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
    form = PoolScopedDateRangeForm(request.GET or None, user=request.user)
    if not form.is_valid():
        return redirect("reports:attendances")
    return attendances_csv(*form.resolved_range(), pool=form.resolved_pool())


@staff_required
def revenue_report_view(request):
    form = RevenueFilterForm(request.GET or None, user=request.user)
    report = None
    if request.GET:
        if form.is_valid():
            report = revenue_report(
                *form.resolved_range(),
                pool=form.resolved_pool(),
                created_by=form.resolved_created_by(),
            )
    else:
        start, end = default_month_range()
        form = RevenueFilterForm(
            initial={"date_from": start, "date_to": end},
            user=request.user,
        )
        report = revenue_report(
            start, end, pool=_default_pool_for_user(request.user)
        )
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
    form = RevenueFilterForm(request.GET or None, user=request.user)
    if not form.is_valid():
        return redirect("reports:revenue")
    return payments_csv(
        *form.resolved_range(),
        pool=form.resolved_pool(),
        created_by=form.resolved_created_by(),
    )


@staff_required
def expiring_report_view(request):
    form = ExpiringDaysForm(request.GET or None, user=request.user)
    within_days = 30
    pool = _default_pool_for_user(request.user)
    if request.GET and form.is_valid():
        within_days = form.cleaned_data["within_days"]
        pool = form.resolved_pool()
    rows = expiring_memberships(within_days, pool=pool)
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
    form = ExpiringDaysForm(request.GET or None, user=request.user)
    if not form.is_valid():
        return redirect("reports:expiring")
    return expiring_csv(
        form.cleaned_data["within_days"],
        pool=form.resolved_pool(),
    )

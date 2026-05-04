from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from checkin.services import evaluate_checkin

from .models import Attendance


class AttendanceAdminForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = "__all__"

    def clean(self):
        cleaned = super().clean()
        client = cleaned.get("client")
        attendance_date = cleaned.get("attendance_date")
        if not client or not attendance_date:
            return cleaned

        inst = self.instance
        if inst.pk:
            same_slot = (
                inst.client_id == client.pk
                and inst.attendance_date == attendance_date
            )
            if same_slot:
                return cleaned

        result = evaluate_checkin(client.access_number, on_date=attendance_date)
        if not result.allowed:
            raise ValidationError(result.message)
        return cleaned

from unfold.widgets import UnfoldAdminCheckboxSelectMultipleWidget


class WeekdaysCheckboxWidget(UnfoldAdminCheckboxSelectMultipleWidget):
    """Checkboxes de días de la semana en fila horizontal (estilo Unfold)."""

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["radio_style"] = 1
        return context

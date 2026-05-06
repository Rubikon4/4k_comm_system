from django import forms


class BootstrapMixin:
    """Добавляет класс Bootstrap form-control ко всем виджетам формы."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            css_class = 'form-check-input' if isinstance(widget, (forms.CheckboxInput, forms.CheckboxSelectMultiple)) else 'form-control'
            widget.attrs.setdefault('class', css_class)

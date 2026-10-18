import unicodedata

from django import forms

from .models import Order


class CustomerForm(forms.Form):
    full_name = forms.CharField(label="Nombre completo", max_length=120)
    delivery_mode = forms.ChoiceField(label="Modalidad de entrega", choices=Order.Delivery.choices,
                                      initial=Order.Delivery.PICKUP, widget=forms.RadioSelect)
    street = forms.CharField(label="Calle", max_length=160, required=False)
    number = forms.CharField(label="Número", max_length=30, required=False)
    city = forms.CharField(label="Ciudad", max_length=100, required=False, initial="Viedma")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["full_name"].widget.attrs["autocomplete"] = "name"
        for name, field in self.fields.items():
            field.error_messages["required"] = "Completá este campo."
            field.widget.attrs["aria-describedby"] = f"id_{name}_error"
        if self.is_bound and self.data.get("delivery_mode") == Order.Delivery.PICKUP:
            # Datos ocultos/maliciosos no participan de la validación ni de la persistencia.
            for name in ("street", "number", "city"):
                self.fields[name].disabled = True
                self.fields[name].initial = ""

    def clean(self):
        data = super().clean()
        for name in ("full_name", "street", "number", "city"):
            value = "".join(c for c in data.get(name, "") if unicodedata.category(c) != "Cf" and (not unicodedata.category(c).startswith("C") or c.isspace()))
            data[name] = " ".join(value.replace("\x00", "").split())
        if not data.get("full_name") and "full_name" not in self.errors:
            self.add_error("full_name", "Ingresá tu nombre completo.")
        if data.get("delivery_mode") == Order.Delivery.DELIVERY:
            for name in ("street", "number", "city"):
                if not data.get(name) and name not in self.errors:
                    self.add_error(name, "Completá este campo para el envío.")
        else:
            for name in ("street", "number", "city"):
                data[name] = ""
        return data

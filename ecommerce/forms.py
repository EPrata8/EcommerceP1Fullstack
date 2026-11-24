from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import Produto, Vendedor


def estilizar(form):
    for c in form.fields.values():
        sel = isinstance(c.widget, forms.Select)
        c.widget.attrs["class"] = "form-select" if sel else "form-control"


class ProdutoForm(forms.ModelForm):
    class Meta:
        model = Produto
        fields = ["nome", "descricao", "preco", "estoque", "vendedor"]

    def __init__(self, *args, org=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["vendedor"].queryset = (
            Vendedor.objects.filter(organizacao=org) if org is not None else Vendedor.objects.none()
        )
        self.fields["descricao"].widget.attrs["rows"] = 3
        estilizar(self)


class PeriodoForm(forms.Form):
    inicio = forms.DateField(
        required=False, widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"})
    )
    fim = forms.DateField(
        required=False, widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        estilizar(self)

    def clean(self):
        d = super().clean()
        ini, fim = d.get("inicio"), d.get("fim")
        if ini and fim and ini > fim:
            raise forms.ValidationError("A data inicial não pode ser maior que a final.")
        return d


class EntrarForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        estilizar(self)


class CadastroForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        estilizar(self)


def filtrar_periodo(request, qs, campo_data="criado_em__date"):
    form = PeriodoForm(request.GET)
    if form.is_valid():
        ini, fim = form.cleaned_data["inicio"], form.cleaned_data["fim"]
        if ini:
            qs = qs.filter(**{f"{campo_data}__gte": ini})
        if fim:
            qs = qs.filter(**{f"{campo_data}__lte": fim})
    return qs

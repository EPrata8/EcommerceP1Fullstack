<<<<<<< HEAD
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
=======
from django import forms
from .models import Produto

class ProdutoForm(forms.ModelForm):
    class Meta:
        model = Produto
        fields = ['nome', 'descricao', 'preco', 'estoque', 'organizacao', 'vendedor']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control bg-dark text-light border-secondary'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control bg-dark text-light border-secondary', 'rows': 3}),
            'preco': forms.NumberInput(attrs={'class': 'form-control bg-dark text-light border-secondary', 'step': '0.01'}),
            'estoque': forms.NumberInput(attrs={'class': 'form-control bg-dark text-light border-secondary'}),
            'organizacao': forms.Select(attrs={'class': 'form-select bg-dark text-light border-secondary'}),
            'vendedor': forms.Select(attrs={'class': 'form-select bg-dark text-light border-secondary'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        preco = cleaned_data.get('preco')
        estoque = cleaned_data.get('estoque')
        
        if preco is not None and preco <= 0:
            raise forms.ValidationError("O preço do produto deve ser maior que zero.")
            
        if estoque is not None and estoque < 0:
            raise forms.ValidationError("A quantidade em stock não pode ser negativa.")
            
        return cleaned_data
>>>>>>> 3a39be6964b3f167629dc8b6025f92803e5a3fe4

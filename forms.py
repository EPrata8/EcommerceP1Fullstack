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
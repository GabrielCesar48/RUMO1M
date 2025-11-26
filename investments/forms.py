from django import forms
from .models import Aporte

class AporteForm(forms.ModelForm):
    class Meta:
        model = Aporte
        fields = ['data', 'valor', 'descricao']
        widgets = {
            'data': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control form-control-lg',
            }),
            'valor': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0',
            }),
            'descricao': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Ex: Salário, Freela, Bônus...',
            }),
        }
        labels = {
            'data': 'Data do Aporte',
            'valor': 'Valor (R$)',
            'descricao': 'Descrição (opcional)',
        }
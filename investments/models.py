from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal

class Aporte(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='aportes')
    data = models.DateField()
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    valor_corrigido = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    descricao = models.CharField(max_length=100, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['data']  # importante para projeção temporal correta

    def __str__(self):
        return f"{self.data.strftime('%d/%m/%Y')} - R$ {self.valor}"

    def corrigir_valor(self, fator):
        """Aplica inflação ao valor original."""
        self.valor_corrigido = Decimal(self.valor) * Decimal(fator)
        self.save()

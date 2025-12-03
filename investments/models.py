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

class TipoAtivo(models.TextChoices):
    ACOES = 'ACOES', 'Ações'
    FUNDOS = 'FUNDOS', 'Fundos de Investimento'
    FIIS = 'FIIS', 'FIIs'
    CRIPTOMOEDAS = 'CRIPTOMOEDAS', 'Criptomoedas'
    BDRS = 'BDRS', 'BDRs'
    ETFS = 'ETFS', 'ETFs'
    TESOURO = 'TESOURO', 'Tesouro Direto'
    RENDA_FIXA = 'RENDA_FIXA', 'Renda Fixa'
    OUTROS = 'OUTROS', 'Outros'

class TipoOperacao(models.TextChoices):
    COMPRA = 'COMPRA', 'Compra'
    VENDA = 'VENDA', 'Venda'

class Lancamento(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lancamentos')
    tipo_operacao = models.CharField(max_length=10, choices=TipoOperacao.choices)
    tipo_ativo = models.CharField(max_length=20, choices=TipoAtivo.choices)
    
    # Dados do ativo
    ticker = models.CharField(max_length=20, blank=True)  # Para ativos com API
    nome_ativo = models.CharField(max_length=200)
    
    # Dados da operação
    data = models.DateField()
    quantidade = models.DecimalField(max_digits=18, decimal_places=8)  # Suporta cripto
    preco = models.DecimalField(max_digits=12, decimal_places=2)
    custos = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Campos específicos para Renda Fixa
    emissor = models.CharField(max_length=200, blank=True)
    tipo_renda_fixa = models.CharField(max_length=50, blank=True)  # CDB, LCI, etc
    indexador = models.CharField(max_length=50, blank=True)  # CDI, IPCA, etc
    data_vencimento = models.DateField(null=True, blank=True)
    liquidez_diaria = models.BooleanField(default=False)
    
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-data', '-criado_em']
        verbose_name = 'Lançamento'
        verbose_name_plural = 'Lançamentos'
    
    def __str__(self):
        return f"{self.tipo_operacao} - {self.nome_ativo} - {self.data.strftime('%d/%m/%Y')}"
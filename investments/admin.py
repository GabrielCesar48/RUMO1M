from django.contrib import admin
from .models import Aporte, Lancamento    

@admin.register(Aporte)
class AporteAdmin(admin.ModelAdmin):
    list_display = ['data', 'valor', 'usuario', 'descricao']
    list_filter = ['usuario', 'data']
    search_fields = ['descricao']


@admin.register(Lancamento)
class LancamentoAdmin(admin.ModelAdmin):
    list_display = ['data', 'tipo_operacao', 'tipo_ativo', 'nome_ativo', 'quantidade', 'preco', 'total', 'usuario']
    list_filter = ['tipo_operacao', 'tipo_ativo', 'usuario', 'data']
    search_fields = ['nome_ativo', 'ticker', 'emissor']
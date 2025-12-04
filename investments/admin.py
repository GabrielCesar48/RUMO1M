from django.contrib import admin
from .models import Aporte, Lancamento, PlanejamentoMensal

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


@admin.register(PlanejamentoMensal)
class PlanejamentoMensalAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'valor_planejado', 'data_inicio', 'atualizado_em', 'valor_corrigido_display']
    list_filter = ['data_inicio']
    search_fields = ['usuario__username']
    readonly_fields = ['data_inicio', 'valor_corrigido_display']
    
    def valor_corrigido_display(self, obj):
        return f"R$ {obj.calcular_valor_corrigido():.2f}"
    valor_corrigido_display.short_description = 'Valor Corrigido Hoje'

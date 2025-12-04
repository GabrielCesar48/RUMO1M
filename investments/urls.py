from django.urls import path
from . import views

urlpatterns = [
    path('adicionar/', views.adicionar_aporte, name='adicionar_aporte'),
    path('editar/<int:pk>/', views.editar_aporte, name='editar_aporte'),
    path('deletar/<int:pk>/', views.deletar_aporte, name='deletar_aporte'),
    
    # PLANEJAMENTO MENSAL - CORRIGIDO!
    path('planejamento/', views.configurar_planejamento, name='configurar_planejamento'),
    
    path('api/buscar-ativos/', views.buscar_ativos_api, name='buscar_ativos_api'),
    path('api/buscar-cotacao/', views.buscar_cotacao_api, name='buscar_cotacao_api'),
    path('api/salvar-lancamentos/', views.salvar_lancamentos, name='salvar_lancamentos'),
    
    path('valuation/', views.valuation_page, name='valuation'),
    path('api/buscar-acoes-valuation/', views.buscar_acoes_valuation_api, name='buscar_acoes_valuation_api'),
    path('api/calcular-valuation/', views.calcular_valuation_api, name='calcular_valuation_api'),
]
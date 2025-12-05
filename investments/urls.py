from django.urls import path
from . import views

urlpatterns = [
    # APORTES (legado)
    path('adicionar/', views.adicionar_aporte, name='adicionar_aporte'),
    path('editar/<int:pk>/', views.editar_aporte, name='editar_aporte'),
    path('deletar/<int:pk>/', views.deletar_aporte, name='deletar_aporte'),
    
    # LANÇAMENTOS (novo sistema)
    path('lancamento/editar/<int:pk>/', views.editar_lancamento, name='editar_lancamento'),
    path('lancamento/deletar/<int:pk>/', views.deletar_lancamento, name='deletar_lancamento'),
    
    # PLANEJAMENTO MENSAL
    path('planejamento/', views.configurar_planejamento, name='configurar_planejamento'),
    
    # APIs
    path('api/buscar-ativos/', views.buscar_ativos_api, name='buscar_ativos_api'),
    path('api/buscar-cotacao/', views.buscar_cotacao_api, name='buscar_cotacao_api'),
    path('api/salvar-lancamentos/', views.salvar_lancamentos, name='salvar_lancamentos'),
    
    # VALUATION
    path('valuation/', views.valuation_page, name='valuation'),
    path('api/buscar-acoes-valuation/', views.buscar_acoes_valuation_api, name='buscar_acoes_valuation_api'),
    path('api/calcular-valuation/', views.calcular_valuation_api, name='calcular_valuation_api'),
]
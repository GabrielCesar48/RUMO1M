from django.urls import path
from . import views

urlpatterns = [
    path('adicionar/', views.adicionar_aporte, name='adicionar_aporte'),
    path('editar/<int:pk>/', views.editar_aporte, name='editar_aporte'),
    path('deletar/<int:pk>/', views.deletar_aporte, name='deletar_aporte'),
]
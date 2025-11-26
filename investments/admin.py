from django.contrib import admin
from .models import Aporte

@admin.register(Aporte)
class AporteAdmin(admin.ModelAdmin):
    list_display = ['data', 'valor', 'usuario', 'descricao']
    list_filter = ['usuario', 'data']
    search_fields = ['descricao']
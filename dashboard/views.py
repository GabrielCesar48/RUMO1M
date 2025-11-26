from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from investments.models import Aporte
from investments.services.inflacao import corrigir_historico, calcular_proximo_aporte
from investments.services.projecao import projetar_futuro
from datetime import datetime

@login_required
def dashboard(request):
    aportes = Aporte.objects.filter(usuario=request.user).order_by("data")

    if aportes.exists():

        # Mantido igual estava antes
        historico_corrigido, fator = corrigir_historico(aportes)
        total = sum(a.valor for a in aportes)
        qtd_aportes = len(aportes)

        # NOVO — já com verificação de IPCA inexistente
        proximo_sugerido = calcular_proximo_aporte(aportes)

        # Se o IPCA do último mês ainda não foi publicado
        if proximo_sugerido is None:
            mes = datetime.now().month
            ano = datetime.now().year
            proximo_display = f"Ainda não há IPCA divulgado para {mes:02d}/{ano}. Aguarde publicação oficial."
            projecao = []  # não calcula projeção enquanto o aporte não pode ser estimado
        else:
            proximo_display = f"R$ {proximo_sugerido:.2f}"

            # corrigindo o erro TypeError — adicionando aumento_anual
            projecao = projetar_futuro(proximo_sugerido, 120, 6)

    else:
        historico_corrigido = []
        projecao = []
        total = 0
        qtd_aportes = 0
        proximo_display = "Nenhum aporte registrado ainda."

    return render(request, "dashboard/home.html", {
        "historico_corrigido": historico_corrigido,
        "projecao": projecao,
        "total": round(total,2),
        "qtd_aportes": qtd_aportes,
        "proximo_sugerido": proximo_display,  # <— agora recebe string ou valor
        "aportes": aportes,
    })

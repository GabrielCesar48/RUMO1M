from datetime import date
from dateutil.relativedelta import relativedelta
from calendar import monthrange
import requests
from decimal import Decimal

# ------------------------------------------------------------
# BUSCA IPCA NO BCB (usa formato DD/MM/YYYY e faz fallback)
# ------------------------------------------------------------
def buscar_ipca(ano, mes, tentativas_max=12):
    """
    Busca o IPCA para (ano, mes) consultando o BCB e validando a data de cada item.
    Retorna Decimal(0.00) se não encontrar dentro das tentativas.
    """

    tentativas = 0
    ano_busca, mes_busca = ano, mes
    
    ultimo_dia = monthrange(ano_busca, mes_busca)[1]

    while tentativas < tentativas_max:
        # Formato DD/MM/YYYY — o BCB aceita
        url = (
                f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.433/dados?"
                f"formato=json&dataInicial=01/{mes_busca:02d}/{ano_busca}&dataFinal={ultimo_dia:02d}/{mes_busca:02d}/{ano_busca}"
            )
        try:
            resp = requests.get(url, timeout=6).json()
        except Exception as e:
            # erro de rede/parsing → aborta e retorna 0
            print(f"[ERRO REQ IPCA] {ano_busca}-{mes_busca}: {e}")
            return Decimal("0.00")

        # valida se veio lista
        if not isinstance(resp, list) or len(resp) == 0:
            # retrocede um mês e tenta de novo
            dt = date(ano_busca, mes_busca, 1) - relativedelta(months=1)
            ano_busca, mes_busca = dt.year, dt.month
            tentativas += 1
            continue

        # filtragem explícita: pegar apenas itens cujo campo "data" pertence ao mês/ano desejado
        itens_mes = []
        for item in resp:
            d = item.get("data", "")
            # espera formato "DD/MM/YYYY"
            try:
                dia_s, mes_s, ano_s = d.split("/")
                ano_i = int(ano_s)
                mes_i = int(mes_s)
            except Exception:
                continue

            if ano_i == ano and mes_i == mes:
                itens_mes.append(item)

        # se achar linhas exatamente do mês/ano pedido, usa a última dessas linhas
        if itens_mes:
            valor_str = itens_mes[-1].get("valor", "0").replace(",", ".")
            try:
                return Decimal(valor_str) / 100
            except Exception:
                # parse falhou → fallback a zero
                return Decimal("0.00")

        # se não encontrou item exatamente do (ano,mes) (estranho), pega a última linha retornada
        # mas loga para debug — geralmente isso não deve acontecer
        try:
            valor_fallback = resp[-1].get("valor", "0").replace(",", ".")
            print(f"[WARN] Resp BCB retornou registros mas nenhum com {mes:02d}/{ano}. Usando último: {valor_fallback}")
            return Decimal(valor_fallback) / 100
        except Exception:
            # tudo falhou → retrocede e tenta novamente
            dt = date(ano_busca, mes_busca, 1) - relativedelta(months=1)
            ano_busca, mes_busca = dt.year, dt.month
            tentativas += 1
            continue

    # se passou todas as tentativas → retorna 0
    print(f"[ERRO IPCA] Não encontrou IPCA para {mes}/{ano} após retroceder {tentativas_max} meses.")
    return None


# ------------------------------------------------------------
# UTILS: calcula fator de correção do mês de inicio até mês 'ate' (não inclusive)
# Ex.: para começar em 2025-06 e ate = 2025-08, aplica IPCA de Jun e Jul (para avançar a 08)
# ------------------------------------------------------------
def fator_correção_ate(ano_inicio, mes_inicio, ano_ate, mes_ate):
    """
    Retorna Decimal fator que deve multiplicar o valor nominal para corrigi-lo
    desde (ano_inicio, mes_inicio) até (ano_ate, mes_ate).
    A lógica: para avançar um mês, aplica-se o IPCA do mês corrente (mês_inicio),
    então avança. Repete até (ano_ate, mes_ate) ser alcançado.
    """
    fator = Decimal(1)
    ano, mes = ano_inicio, mes_inicio

    # enquanto (ano,mes) < (ano_ate, mes_ate) aplicar ipca do mês atual e avançar
    while (ano < ano_ate) or (ano == ano_ate and mes < mes_ate):
        ipca = buscar_ipca(ano, mes)
        fator *= (1 + ipca)
        prox = date(ano, mes, 1) + relativedelta(months=1)
        ano, mes = prox.year, prox.month

    return fator


# ------------------------------------------------------------
# Corrige o histórico de aportes até o mês atual e salva valor_corrigido (opcional)
# ------------------------------------------------------------
def corrigir_historico(aportes, salvar=True):
    """
    Recebe queryset de aportes ordenados por data (ou não) e retorna:
      historico: lista de valores corrigidos (float) na ordem cronológica dos aportes
      fator_total: fator acumulado até o mês atual (float), referente ao último aporte
    Observação: para cada aporte, corrige desde seu mês até o mês atual (aplicando IPCA mês a mês).
    """
    hoje = date.today()
    ano_ate, mes_ate = hoje.year, hoje.month

    historico = []
    fator_total = Decimal(1)

    for aporte in aportes.order_by("data"):
        ano0, mes0 = aporte.data.year, aporte.data.month
        fator = fator_correção_ate(ano0, mes0, ano_ate, mes_ate)
        corrigido = Decimal(aporte.valor) * fator
        historico.append(float(corrigido))

        if salvar:
            # tenta salvar valor_corrigido se o campo existir no model
            try:
                aporte.valor_corrigido = corrigido
                aporte.save(update_fields=["valor_corrigido"])
            except Exception:
                # se o model não tiver o campo, ignora
                pass

        fator_total = fator  # último fator corresponde ao último aporte

    return historico, float(fator_total)


# ------------------------------------------------------------
# Calcula o próximo aporte sugerido a partir do último aporte
# Aplicando IPCA do mês anterior para cada avanço de mês até o mês atual
# ------------------------------------------------------------
from datetime import date
from dateutil.relativedelta import relativedelta
from decimal import Decimal

def calcular_proximo_aporte(aportes):
    aportes = aportes.order_by("data")
    ultimo = aportes.last()

    valor_base = Decimal(ultimo.valor)

    # determina o mês do próximo aporte
    prox = ultimo.data + relativedelta(months=1)
    ano, mes = prox.year, prox.month

    # tenta buscar IPCA desse mês
    ipca = buscar_ipca(ano, mes)

    if ipca is None or ipca == 0:
        return None

    # se tiver IPCA → corrige
    return round(float(valor_base * (1 + ipca)), 2)

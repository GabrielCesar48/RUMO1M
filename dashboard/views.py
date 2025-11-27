from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from investments.models import Aporte
from investments.services.inflacao import calcular_proximo_aporte
from datetime import datetime
from decimal import Decimal

@login_required
def dashboard(request):
    aportes = Aporte.objects.filter(usuario=request.user).order_by("data")

    if aportes.exists():
        # Calcular acumulado mês a mês
        historico_acumulado = []
        acumulado = 0
        for aporte in aportes:
            acumulado += float(aporte.valor)
            historico_acumulado.append(round(acumulado, 2))
        
        total = acumulado
        qtd_aportes = len(aportes)
        media_mensal = total / qtd_aportes if qtd_aportes > 0 else 0
        maior_aporte = max(float(a.valor) for a in aportes)

        # Badges - calcular qual está ativo
        badges = calcular_badges(total)

        # SEMPRE CALCULAR PROJEÇÕES (usando média mensal)
        meses_projecao = 120
        aporte_mensal = media_mensal
        
        # DEBUG
        print(f"\n=== DEBUG PROJEÇÃO ===")
        print(f"Total atual: R$ {total:.2f}")
        print(f"Aporte mensal (média): R$ {aporte_mensal:.2f}")
        print(f"Meses para projetar: {meses_projecao}")
        
        # Calcular 3 cenários COMEÇANDO DO SALDO ATUAL
        projecao_conservador = calcular_projecao(total, aporte_mensal, meses_projecao, 0.08)
        projecao_moderado = calcular_projecao(total, aporte_mensal, meses_projecao, 0.12)
        projecao_agressivo = calcular_projecao(total, aporte_mensal, meses_projecao, 0.14)
        
        # DEBUG
        print(f"Conservador - Primeiros 5 meses: {projecao_conservador[:5]}")
        print(f"Conservador - Último valor (10 anos): R$ {projecao_conservador[-1]:.2f}")
        print(f"Moderado - Último valor (10 anos): R$ {projecao_moderado[-1]:.2f}")
        print(f"Agressivo - Último valor (10 anos): R$ {projecao_agressivo[-1]:.2f}")
        print(f"=====================\n")

        # Próximo aporte sugerido (separado da projeção)
        proximo_sugerido = calcular_proximo_aporte(aportes)
        
        if proximo_sugerido is None:
            mes = datetime.now().month
            ano = datetime.now().year
            proximo_valor = None
            proximo_mensagem = f"IPCA de {mes:02d}/{ano} ainda não foi divulgado pelo BCB. Aguarde a publicação oficial."
        else:
            proximo_valor = proximo_sugerido
            proximo_mensagem = None

        context = {
            "historico_acumulado": historico_acumulado,
            "projecao_conservador": projecao_conservador,
            "projecao_moderado": projecao_moderado,
            "projecao_agressivo": projecao_agressivo,
            "total": round(total, 2),
            "qtd_aportes": qtd_aportes,
            "media_mensal": round(media_mensal, 2),
            "maior_aporte": round(maior_aporte, 2),
            "proximo_valor": proximo_valor,
            "proximo_mensagem": proximo_mensagem,
            "badges": badges,
            "aportes": aportes[:10],
        }
    else:
        context = {
            "historico_acumulado": [],
            "projecao_conservador": [],
            "projecao_moderado": [],
            "projecao_agressivo": [],
            "total": 0,
            "qtd_aportes": 0,
            "media_mensal": 0,
            "maior_aporte": 0,
            "proximo_valor": None,
            "proximo_mensagem": "Adicione seu primeiro aporte para começar!",
            "badges": calcular_badges(0),
            "aportes": [],
        }

    return render(request, "dashboard/home.html", context)


def calcular_projecao(saldo_inicial, aporte_mensal, meses, taxa_anual):
    """
    Calcula projeção com juros compostos.
    
    Args:
        saldo_inicial: patrimônio atual
        aporte_mensal: valor que será aportado todo mês
        meses: quantos meses projetar
        taxa_anual: taxa de juros anual (ex: 0.12 = 12%)
    
    Returns:
        lista com valores acumulados mês a mês
    """
    taxa_mensal = (1 + taxa_anual) ** (1/12) - 1
    saldo = Decimal(str(saldo_inicial))
    aporte = Decimal(str(aporte_mensal))
    
    projecao = []
    
    for mes in range(1, meses + 1):
        # Aplica juros sobre o saldo
        saldo = saldo * (1 + Decimal(str(taxa_mensal)))
        # Adiciona novo aporte
        saldo = saldo + aporte
        projecao.append(round(float(saldo), 2))
    
    return projecao


def calcular_badges(total):
    """
    Calcula os badges de progresso baseado no total investido.
    
    Returns:
        dict com informações do badge atual
    """
    marcos = [
        # Valor, Título, Mensagem, Emoji, Cor
        (1000, "Primeiro Passo", "Você começou sua jornada! 🎯", "🎯", "primary"),
        (3000, "Acelerando", "Consistência é a chave! 💪", "💪", "info"),
        (5000, "5k Investidos", "Você está no caminho certo! 🚀", "🚀", "success"),
        (8000, "Quase 10k", "Continue assim! 🔥", "🔥", "warning"),
        (10000, "10k Alcançados", "Primeiro marco importante! 💎", "💎", "success"),
        (15000, "15k Investidos", "Crescendo forte! 📈", "📈", "info"),
        (20000, "20k Alcançados", "Momentum crescente! ⚡", "⚡", "warning"),
        (25000, "Rumo aos 30k", "Sem parar agora! 🏃", "🏃", "primary"),
        (30000, "30k Investidos", "Você é determinado! 🎖️", "🎖️", "success"),
        (40000, "40k Alcançados", "Acumulando poder! 💪", "💪", "info"),
        (50000, "50k Investidos", "Meio caminho para 100k! 🎊", "🎊", "warning"),
        (60000, "60k Alcançados", "Exponencial começa agora! 📊", "📊", "success"),
        (70000, "70k Investidos", "Nada te para! 🚂", "🚂", "primary"),
        (80000, "80k Alcançados", "Quase nos 6 dígitos! 🤩", "🤩", "info"),
        (90000, "90k Investidos", "Falta tão pouco para 100k! 🔥", "🔥", "warning"),
        (100000, "100k - Incrível!", "Você está a 1/10 do primeiro milhão! 👑", "👑", "success"),
        (150000, "150k Investidos", "Juros compostos trabalhando! 💰", "💰", "info"),
        (200000, "200k Alcançados", "1/5 do primeiro milhão! 🏆", "🏆", "warning"),
        (250000, "250k Investidos", "1/4 do caminho! 🎯", "🎯", "success"),
        (300000, "300k Alcançados", "Quase 1/3! 🚀", "🚀", "primary"),
        (350000, "350k Investidos", "Imparável! ⚡", "⚡", "info"),
        (400000, "400k Alcançados", "Crescimento exponencial! 📈", "📈", "warning"),
        (450000, "450k Investidos", "Quase na metade! 🔥", "🔥", "success"),
        (500000, "500k - Metade!", "Você chegou na metade! A partir de agora vai ser rápido! 🎉", "🎉", "success"),
        (600000, "600k Investidos", "Mais da metade! 💎", "💎", "info"),
        (700000, "700k Alcançados", "70% completo! 🏃", "🏃", "warning"),
        (800000, "800k Investidos", "80% do caminho! 🚂", "🚂", "primary"),
        (900000, "900k Alcançados", "Falta tão pouco! 🤩", "🤩", "info"),
        (1000000, "1 MILHÃO!", "🎊 VOCÊ CONSEGUIU! PARABÉNS! 🎊", "👑", "success"),
    ]
    
    badge_atual = None
    proximo_badge = marcos[0]
    progresso_percentual = 0
    
    for i, (valor, titulo, mensagem, emoji, cor) in enumerate(marcos):
        if total >= valor:
            badge_atual = {
                "valor": valor,
                "titulo": titulo,
                "mensagem": mensagem,
                "emoji": emoji,
                "cor": cor,
                "alcancado": True
            }
            # Próximo badge
            if i + 1 < len(marcos):
                proximo_badge = {
                    "valor": marcos[i + 1][0],
                    "titulo": marcos[i + 1][1],
                    "mensagem": marcos[i + 1][2],
                    "emoji": marcos[i + 1][3],
                    "cor": marcos[i + 1][4],
                    "alcancado": False
                }
        else:
            proximo_badge = {
                "valor": valor,
                "titulo": titulo,
                "mensagem": mensagem,
                "emoji": emoji,
                "cor": cor,
                "alcancado": False
            }
            break
    
    # Calcular progresso até o próximo badge
    if badge_atual and not proximo_badge["alcancado"]:
        progresso = total - badge_atual["valor"]
        distancia = proximo_badge["valor"] - badge_atual["valor"]
        progresso_percentual = int((progresso / distancia) * 100)
    elif not badge_atual:
        progresso_percentual = int((total / proximo_badge["valor"]) * 100)
    else:
        progresso_percentual = 100
    
    return {
        "atual": badge_atual,
        "proximo": proximo_badge,
        "progresso": min(progresso_percentual, 100),
        "falta": proximo_badge["valor"] - total if total < proximo_badge["valor"] else 0
    }
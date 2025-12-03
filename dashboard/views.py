from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from investments.models import Aporte, Lancamento
from investments.services.inflacao import calcular_proximo_aporte
from datetime import datetime
from decimal import Decimal
from collections import defaultdict
import requests

@login_required
def dashboard(request):
    # Buscar Aportes antigos (se existirem)
    aportes = Aporte.objects.filter(usuario=request.user).order_by("data")
    
    # Buscar Lançamentos (novo sistema)
    lancamentos = Lancamento.objects.filter(usuario=request.user).order_by("data")
    
    # CONSOLIDAR: Somar aportes antigos + lançamentos novos (apenas COMPRA)
    total_aportes_antigos = sum(float(a.valor) for a in aportes)
    total_lancamentos_compras = sum(float(l.total) for l in lancamentos.filter(tipo_operacao='COMPRA'))
    total_investido = total_aportes_antigos + total_lancamentos_compras
    
    # Quantidade total de aportes/compras
    qtd_aportes = aportes.count() + lancamentos.filter(tipo_operacao='COMPRA').count()
    
    # Média mensal
    media_mensal = total_investido / qtd_aportes if qtd_aportes > 0 else 0
    
    # Maior aporte
    maior_aporte_antigo = max((float(a.valor) for a in aportes), default=0)
    maior_lancamento = max((float(l.total) for l in lancamentos.filter(tipo_operacao='COMPRA')), default=0)
    maior_aporte = max(maior_aporte_antigo, maior_lancamento)
    
    if qtd_aportes > 0:
        # Histórico acumulado (aportes + lançamentos em ordem cronológica)
        historico_acumulado = []
        acumulado = 0
        
        # Juntar e ordenar por data
        items = []
        for a in aportes:
            items.append(('aporte', a.data, float(a.valor)))
        for l in lancamentos.filter(tipo_operacao='COMPRA'):
            items.append(('lancamento', l.data, float(l.total)))
        
        items.sort(key=lambda x: x[1])  # Ordenar por data
        
        for tipo, data, valor in items:
            acumulado += valor
            historico_acumulado.append(round(acumulado, 2))
        
        # Badges
        badges = calcular_badges(total_investido)
        
        # Projeções
        meses_projecao = 120
        aporte_mensal = media_mensal
        
        projecao_conservador = calcular_projecao(total_investido, aporte_mensal, meses_projecao, 0.08)
        projecao_moderado = calcular_projecao(total_investido, aporte_mensal, meses_projecao, 0.12)
        projecao_agressivo = calcular_projecao(total_investido, aporte_mensal, meses_projecao, 0.14)

        # Próximo aporte sugerido
        if aportes.exists():
            proximo_sugerido = calcular_proximo_aporte(aportes)
        else:
            # Se não tem aportes, usar média dos lançamentos
            proximo_sugerido = media_mensal if media_mensal > 0 else None
        
        if proximo_sugerido is None:
            mes = datetime.now().month
            ano = datetime.now().year
            proximo_valor = None
            proximo_mensagem = f"IPCA de {mes:02d}/{ano} ainda não foi divulgado pelo BCB."
        else:
            proximo_valor = proximo_sugerido
            proximo_mensagem = None

        # Consolidar carteira
        carteira = consolidar_carteira(request.user)
        
        # Calcular totais da carteira
        total_investido_carteira = sum(float(p['valor_total']) for p in carteira.values())
        total_mercado_carteira = sum(float(p.get('valor_mercado', p['valor_total'])) for p in carteira.values())
        lucro_total = total_mercado_carteira - total_investido_carteira
        rentabilidade = (lucro_total / total_investido_carteira * 100) if total_investido_carteira > 0 else 0
        
        # Diversificação
        diversificacao = {}
        for pos in carteira.values():
            tipo = pos['tipo_ativo']
            nome_tipo = dict(Lancamento._meta.get_field('tipo_ativo').choices).get(tipo, tipo)
            if nome_tipo not in diversificacao:
                diversificacao[nome_tipo] = {'valor': 0, 'percentual': 0}
            diversificacao[nome_tipo]['valor'] += float(pos.get('valor_mercado', pos['valor_total']))
        
        for tipo in diversificacao:
            diversificacao[tipo]['percentual'] = round(
                (diversificacao[tipo]['valor'] / total_mercado_carteira * 100) if total_mercado_carteira > 0 else 0,
                2
            )

        # Últimos lançamentos para exibir
        ultimos_items = []
        for a in aportes[:5]:
            ultimos_items.append({
                'tipo': 'Aporte',
                'data': a.data,
                'valor': a.valor,
                'descricao': a.descricao,
                'id': a.id,
                'is_aporte': True
            })
        for l in lancamentos[:5]:
            ultimos_items.append({
                'tipo': l.get_tipo_operacao_display(),
                'data': l.data,
                'valor': l.total,
                'descricao': l.nome_ativo,
                'id': l.id,
                'is_aporte': False
            })
        ultimos_items.sort(key=lambda x: x['data'], reverse=True)
        ultimos_items = ultimos_items[:10]

        context = {
            "historico_acumulado": historico_acumulado,
            "projecao_conservador": projecao_conservador,
            "projecao_moderado": projecao_moderado,
            "projecao_agressivo": projecao_agressivo,
            "total": round(total_investido, 2),
            "qtd_aportes": qtd_aportes,
            "media_mensal": round(media_mensal, 2),
            "maior_aporte": round(maior_aporte, 2),
            "proximo_valor": proximo_valor,
            "proximo_mensagem": proximo_mensagem,
            "badges": badges,
            "ultimos_items": ultimos_items,
            "carteira": carteira,
            "tem_carteira": len(carteira) > 0,
            "total_investido_carteira": round(total_investido_carteira, 2),
            "total_mercado_carteira": round(total_mercado_carteira, 2),
            "lucro_total": round(lucro_total, 2),
            "rentabilidade": round(rentabilidade, 2),
            "diversificacao": diversificacao,
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
            "proximo_mensagem": "Adicione seu primeiro investimento para começar!",
            "badges": calcular_badges(0),
            "ultimos_items": [],
            "carteira": {},
            "tem_carteira": False,
            "total_investido_carteira": 0,
            "total_mercado_carteira": 0,
            "lucro_total": 0,
            "rentabilidade": 0,
            "diversificacao": {},
        }

    return render(request, "dashboard/home.html", context)


def consolidar_carteira(usuario):
    """Consolida todas as operações em posições atuais"""
    lancamentos = Lancamento.objects.filter(usuario=usuario).order_by('data')
    
    posicoes = defaultdict(lambda: {
        'quantidade': Decimal('0'),
        'valor_medio': Decimal('0'),
        'valor_total': Decimal('0'),
        'tipo_ativo': '',
        'ticker': '',
        'nome': '',
        'logo': ''
    })
    
    for lanc in lancamentos:
        chave = lanc.ticker or lanc.nome_ativo
        
        if lanc.tipo_operacao == 'COMPRA':
            posicoes[chave]['quantidade'] += lanc.quantidade
            posicoes[chave]['valor_total'] += lanc.total
            if posicoes[chave]['quantidade'] > 0:
                posicoes[chave]['valor_medio'] = posicoes[chave]['valor_total'] / posicoes[chave]['quantidade']
        else:
            posicoes[chave]['quantidade'] -= lanc.quantidade
            if posicoes[chave]['quantidade'] > 0:
                posicoes[chave]['valor_total'] = posicoes[chave]['valor_medio'] * posicoes[chave]['quantidade']
            else:
                posicoes[chave]['valor_total'] = Decimal('0')
        
        posicoes[chave]['tipo_ativo'] = lanc.tipo_ativo
        posicoes[chave]['ticker'] = lanc.ticker
        posicoes[chave]['nome'] = lanc.nome_ativo
    
    # Buscar dados atualizados da API
    for chave, pos in list(posicoes.items()):
        if pos['quantidade'] <= 0:
            del posicoes[chave]
            continue
            
        if pos['ticker']:
            try:
                url = f"https://brapi.dev/api/quote/{pos['ticker']}"
                response = requests.get(url, timeout=3)
                if response.ok:
                    data = response.json()
                    if 'results' in data and len(data['results']) > 0:
                        resultado = data['results'][0]
                        pos['logo'] = resultado.get('logourl', '')
                        pos['preco_atual'] = Decimal(str(resultado.get('regularMarketPrice', 0)))
                        pos['valor_mercado'] = pos['preco_atual'] * pos['quantidade']
                        pos['lucro_prejuizo'] = pos['valor_mercado'] - pos['valor_total']
                        pos['rentabilidade'] = ((pos['valor_mercado'] / pos['valor_total'] - 1) * 100) if pos['valor_total'] > 0 else 0
            except:
                pass
    
    return dict(posicoes)


def calcular_projecao(saldo_inicial, aporte_mensal, meses, taxa_anual):
    taxa_mensal = (1 + taxa_anual) ** (1/12) - 1
    saldo = Decimal(str(saldo_inicial))
    aporte = Decimal(str(aporte_mensal))
    
    projecao = []
    for mes in range(1, meses + 1):
        saldo = saldo * (1 + Decimal(str(taxa_mensal)))
        saldo = saldo + aporte
        projecao.append(round(float(saldo), 2))
    
    return projecao


def calcular_badges(total):
    marcos = [
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
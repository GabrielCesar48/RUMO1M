"""
Serviço de Valuation com OpenAI
- Extrai dados do Investidor10
- Análise IA especialista
- Resumo de notícias
"""

import os
import json
from decimal import Decimal
from openai import OpenAI
from datetime import datetime, timedelta
from decouple import config

client = OpenAI(api_key=config('OPENAI_API_KEY'))


def extrair_dados_investidor10(ticker: str):
    """Extrai dados fundamentalistas do Investidor10 via OpenAI"""
    url = f"https://investidor10.com.br/acoes/{ticker.lower()}/"
    
    prompt = f"""
Acesse {url} e extraia:

DADOS OBRIGATÓRIOS:
- preco (cotação atual)
- lpa (Lucro por Ação)
- pl (P/L)
- roe (ROE em %)
- dy (Dividend Yield em %)
- vpa (Valor Patrimonial)

REGRAS:
- Retorne APENAS JSON
- Use null se não encontrar
- Valores percentuais sem o símbolo %
- Valores monetários em número decimal

Ticker: {ticker.upper()}

JSON:
"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Você extrai dados do Investidor10. Retorne apenas JSON válido."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=300
        )
        
        conteudo = response.choices[0].message.content.strip()
        
        if conteudo.startswith("```"):
            conteudo = conteudo.split("```")[1]
            if conteudo.startswith("json"):
                conteudo = conteudo[4:]
        
        dados = json.loads(conteudo.strip())
        
        if not dados.get('preco') or not dados.get('lpa'):
            return None
        
        return {
            'ticker': ticker.upper(),
            'preco': float(dados['preco']),
            'lpa': float(dados['lpa']) if dados.get('lpa') else 0,
            'pl': float(dados['pl']) if dados.get('pl') else 0,
            'roe': float(dados['roe']) if dados.get('roe') else 0,
            'dy': float(dados['dy']) if dados.get('dy') else 0,
            'vpa': float(dados['vpa']) if dados.get('vpa') else 0,
        }
        
    except Exception as e:
        print(f"[ERRO] Extração: {e}")
        return None


def gerar_analise_ia(ticker: str, dados: dict):
    """Gera análise profissional via IA especialista"""
    
    prompt = f"""
Você é um analista financeiro sênior com 20 anos de experiência no mercado brasileiro.

DADOS DA AÇÃO {ticker}:
- Preço: R$ {dados['preco']:.2f}
- LPA: R$ {dados['lpa']:.2f}
- P/L: {dados['pl']:.2f}x
- ROE: {dados['roe']:.2f}%
- Dividend Yield: {dados['dy']:.2f}%
- VPA: R$ {dados['vpa']:.2f}

TAREFA:
Escreva uma análise profissional e objetiva em até 300 palavras cobrindo:
1. Avaliação geral da ação (cara/barata/justa)
2. Pontos fortes
3. Pontos fracos ou riscos
4. Recomendação final (curto/médio/longo prazo)

IMPORTANTE:
- Use linguagem profissional mas acessível
- Seja direto e objetivo
- NÃO mencione métodos de valuation específicos
- NÃO dê recomendações de compra/venda diretas
- Foque em análise fundamentalista
"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Você é um analista financeiro sênior especializado em ações brasileiras."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        print(f"[ERRO] Análise IA: {e}")
        return "Análise não disponível no momento."


def buscar_noticias_resumo(ticker: str):
    """Busca e resume últimas notícias sobre a ação"""
    
    hoje = datetime.now()
    mes_passado = hoje - timedelta(days=30)
    
    prompt = f"""
Busque as 5 notícias mais recentes sobre a ação {ticker} dos últimos 30 dias.

FONTES RECOMENDADAS:
- InfoMoney
- Valor Econômico
- Money Times
- Seu Dinheiro
- Estadão Economia

TAREFA:
Resuma as principais notícias em até 500 palavras, cobrindo:
1. Fatos mais relevantes (resultados, dividendos, mudanças estratégicas)
2. Expectativas do mercado
3. Riscos ou oportunidades mencionados

FORMATO:
Texto corrido, objetivo, sem lista de notícias individuais.

IMPORTANTE:
- Se não encontrar notícias recentes, mencione isso
- Priorize notícias dos últimos 7 dias
- Ignore rumores não confirmados
"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Você é um analista de mercado que resume notícias financeiras."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=700
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        print(f"[ERRO] Notícias: {e}")
        return "Não foi possível buscar notícias no momento."


def calcular_valuation(ticker: str):
    """
    Calcula valuation completo:
    - Dados do Investidor10
    - 3 métodos (Bazin, Graham, Lynch)
    - Análise IA
    - Resumo de notícias
    """
    
    # 1. Extrair dados
    dados = extrair_dados_investidor10(ticker)
    if not dados:
        return None
    
    # 2. Gerar análise IA (paralelo)
    ai_analysis = gerar_analise_ia(ticker, dados)
    
    # 3. Buscar notícias (paralelo)
    news_summary = buscar_noticias_resumo(ticker)
    
    # 4. Calcular métodos
    preco = Decimal(str(dados['preco']))
    lpa = Decimal(str(dados['lpa']))
    pl = Decimal(str(dados['pl']))
    roe = Decimal(str(dados['roe']))
    dy = Decimal(str(dados['dy']))
    vpa = Decimal(str(dados['vpa']))
    
    # ===== BAZIN =====
    bazin_teto = None
    bazin_status = "DADOS_INSUFICIENTES"
    bazin_margem = None
    bazin_formula = "Necessita Dividend Yield"
    
    if dy > 0:
        dpa = (dy / 100) * preco
        bazin_teto = float(dpa / Decimal('0.06'))
        margem = ((Decimal(str(bazin_teto)) - preco) / Decimal(str(bazin_teto))) * 100
        
        if preco <= Decimal(str(bazin_teto)):
            bazin_status = "COMPRAR"
        elif preco <= Decimal(str(bazin_teto)) * Decimal('1.05'):
            bazin_status = "AGUARDAR"
        else:
            bazin_status = "VENDER"
        
        bazin_margem = float(margem)
        bazin_formula = f"DPA (R$ {float(dpa):.2f}) ÷ 6% = R$ {bazin_teto:.2f}"
    
    # ===== GRAHAM =====
    graham_justo = None
    graham_status = "DADOS_INSUFICIENTES"
    graham_margem = None
    graham_formula = "Necessita LPA e VPA"
    
    if lpa > 0 and vpa > 0:
        graham_justo = float((Decimal('22.5') * lpa * vpa).sqrt())
        margem = ((Decimal(str(graham_justo)) - preco) / Decimal(str(graham_justo))) * 100
        
        if preco <= Decimal(str(graham_justo)) * Decimal('0.66'):
            graham_status = "COMPRAR"
        elif preco <= Decimal(str(graham_justo)):
            graham_status = "AGUARDAR"
        else:
            graham_status = "VENDER"
        
        graham_margem = float(margem)
        graham_formula = f"√(22.5 × R$ {float(lpa):.2f} × R$ {float(vpa):.2f}) = R$ {graham_justo:.2f}"
    
    elif lpa > 0:
        graham_justo = float(lpa * 15)
        margem = ((Decimal(str(graham_justo)) - preco) / Decimal(str(graham_justo))) * 100
        
        if preco <= Decimal(str(graham_justo)) * Decimal('0.75'):
            graham_status = "COMPRAR"
        elif preco <= Decimal(str(graham_justo)):
            graham_status = "AGUARDAR"
        else:
            graham_status = "VENDER"
        
        graham_margem = float(margem)
        graham_formula = f"LPA (R$ {float(lpa):.2f}) × 15 = R$ {graham_justo:.2f}"
    
    # ===== LYNCH =====
    lynch_peg = None
    lynch_status = "DADOS_INSUFICIENTES"
    lynch_margem = None
    lynch_ideal = None
    lynch_formula = "Necessita P/L e ROE"
    
    if pl > 0 and roe > 0:
        lynch_peg = float(pl / roe)
        lynch_ideal = float(lpa * roe)
        
        if lynch_ideal > 0:
            margem = ((Decimal(str(lynch_ideal)) - preco) / Decimal(str(lynch_ideal))) * 100
            lynch_margem = float(margem)
        
        if lynch_peg < 0.5:
            lynch_status = "COMPRAR"
        elif lynch_peg <= 1.0:
            lynch_status = "COMPRAR"
        elif lynch_peg <= 1.5:
            lynch_status = "AGUARDAR"
        else:
            lynch_status = "VENDER"
        
        lynch_formula = f"P/L ({float(pl):.2f}) ÷ ROE ({float(roe):.2f}%) = {lynch_peg:.2f}"
    
    # ===== RECOMENDAÇÃO =====
    metodos_validos = [s for s in [bazin_status, graham_status, lynch_status] if s != "DADOS_INSUFICIENTES"]
    
    if len(metodos_validos) == 0:
        status_geral = "DADOS_INSUFICIENTES"
        votos_compra = 0
        votos_venda = 0
    else:
        votos_compra = sum([1 for s in metodos_validos if s == "COMPRAR"])
        votos_venda = sum([1 for s in metodos_validos if s == "VENDER"])
        
        if votos_compra >= len(metodos_validos) / 2:
            status_geral = "COMPRAR"
        elif votos_venda >= len(metodos_validos) / 2:
            status_geral = "VENDER"
        else:
            status_geral = "AGUARDAR"
    
    # ===== RETORNO =====
    return {
        'ticker': dados['ticker'],
        'preco_atual': f"R$ {float(preco):.2f}",
        
        'dados_base': {
            'preco': f"R$ {float(preco):.2f}",
            'lpa': f"R$ {float(lpa):.2f}",
            'pl': f"{float(pl):.2f}x" if pl > 0 else "N/A",
            'roe': f"{float(roe):.2f}%" if roe > 0 else "N/A",
            'dy': f"{float(dy):.2f}%" if dy > 0 else "N/A",
        },
        
        'ai_analysis': ai_analysis,
        'news_summary': news_summary,
        
        'bazin': {
            'preco_teto': f"R$ {bazin_teto:.2f}" if bazin_teto else "N/A",
            'status': bazin_status,
            'margem': f"{bazin_margem:.1f}%" if bazin_margem is not None else "N/A",
            'emoji': '🟢' if bazin_status == 'COMPRAR' else ('🔴' if bazin_status == 'VENDER' else '🟡'),
            'formula': bazin_formula,
        },
        
        'graham': {
            'preco_justo': f"R$ {graham_justo:.2f}" if graham_justo else "N/A",
            'status': graham_status,
            'margem': f"{graham_margem:.1f}%" if graham_margem is not None else "N/A",
            'emoji': '🟢' if graham_status == 'COMPRAR' else ('🔴' if graham_status == 'VENDER' else '🟡'),
            'formula': graham_formula,
        },
        
        'lynch': {
            'peg': f"{lynch_peg:.2f}" if lynch_peg else "N/A",
            'preco_ideal': f"R$ {lynch_ideal:.2f}" if lynch_ideal else "N/A",
            'status': lynch_status,
            'margem': f"{lynch_margem:.1f}%" if lynch_margem is not None else "N/A",
            'emoji': '🟢' if lynch_status == 'COMPRAR' else ('🔴' if lynch_status == 'VENDER' else '🟡'),
            'formula': lynch_formula,
        },
        
        'recomendacao': {
            'status': status_geral,
            'emoji': '🟢' if status_geral == 'COMPRAR' else ('🔴' if status_geral == 'VENDER' else '🟡'),
            'pontos_compra': votos_compra if metodos_validos else 0,
            'pontos_venda': votos_venda if metodos_validos else 0,
        }
    }
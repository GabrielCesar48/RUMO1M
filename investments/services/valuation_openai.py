"""
Serviço de Valuation com Web Scraping OTIMIZADO
- Scraping específico para estrutura do Investidor10
- Análise IA especialista
- Resumo de notícias
"""

import os
import json
import requests
from decimal import Decimal
from openai import OpenAI
from datetime import datetime, timedelta
from decouple import config
from bs4 import BeautifulSoup
import re

client = OpenAI(api_key=config('OPENAI_API_KEY'))


def extrair_dados_investidor10(ticker: str):
    """
    Faz web scraping OTIMIZADO do Investidor10
    Extrai dados fundamentalistas usando estrutura específica do site
    """
    url = f"https://investidor10.com.br/acoes/{ticker.lower()}/"
    
    try:
        print(f"[SCRAPING] Acessando {url}...")
        
        # Headers para simular navegador
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
            'Referer': 'https://www.google.com/',
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            print(f"[ERRO] Status {response.status_code}")
            return None
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Dados a extrair
        dados = {
            'ticker': ticker.upper(),
            'preco': 0,
            'lpa': 0,
            'pl': 0,
            'roe': 0,
            'dy': 0,
            'vpa': 0,
        }
        
        # ESTRATÉGIA: Passar TODO o HTML para a IA e pedir extração
        # É mais confiável que tentar parsear estrutura que pode mudar
        
        print(f"[SCRAPING] HTML baixado, usando IA para extrair dados...")
        
        # Pegar texto completo da página
        texto_pagina = soup.get_text(separator=' ', strip=True)
        
        # Limitar tamanho (GPT-4o aguenta ~128k tokens, mas vamos usar 10k caracteres)
        texto_relevante = texto_pagina[:15000]
        
        # Prompt MUITO específico para extração
        prompt = f"""
Você é um extrator de dados financeiros. Analise este texto da página do Investidor10 sobre a ação {ticker.upper()}.

TEXTO DA PÁGINA:
{texto_relevante}

Extraia APENAS os seguintes indicadores fundamentalistas (use os valores MAIS RECENTES que encontrar):

1. PREÇO/COTAÇÃO atual em reais (procure por "Cotação", "Preço", valores com R$)
2. LPA ou "Lucro por Ação" (em reais, pode estar como "L/A", "LPA", "Lucro p/ Ação")
3. P/L ou "Preço sobre Lucro" (número decimal, pode estar como "P/L", "Preço/Lucro")
4. ROE ou "Retorno sobre Patrimônio" (em %, pode estar como "ROE", "Return on Equity")
5. DY ou "Dividend Yield" (em %, pode estar como "DY", "Div. Yield", "Dividendos")
6. VPA ou "Valor Patrimonial por Ação" (em reais, pode estar como "VPA", "V.P.A", "Valor Patrimonial")

REGRAS IMPORTANTES:
- Retorne APENAS números (sem símbolos de % ou R$)
- Se o ROE for 15%, retorne 15 (não 0.15)
- Se o DY for 8%, retorne 8 (não 0.08)
- Se não encontrar algum valor, use 0
- Para preço, use o valor da cotação mais recente
- Para indicadores, priorize valores anuais (12 meses)

Retorne APENAS este JSON (sem markdown, sem explicação):
{{"preco": 0, "lpa": 0, "pl": 0, "roe": 0, "dy": 0, "vpa": 0}}
"""
        
        try:
            response_ai = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Você é um extrator de dados financeiros preciso. Retorne apenas JSON válido sem markdown."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=300
            )
            
            conteudo = response_ai.choices[0].message.content.strip()
            
            # Limpar markdown se vier
            if conteudo.startswith("```"):
                conteudo = conteudo.split("```")[1]
                if conteudo.startswith("json"):
                    conteudo = conteudo[4:]
                conteudo = conteudo.strip()
            
            # Parse JSON
            dados_extraidos = json.loads(conteudo)
            
            # Atualizar dados
            for chave in ['preco', 'lpa', 'pl', 'roe', 'dy', 'vpa']:
                if chave in dados_extraidos and dados_extraidos[chave]:
                    dados[chave] = float(dados_extraidos[chave])
            
            print(f"[IA EXTRAÇÃO] ✅ Dados extraídos com sucesso")
            
            # Log dos dados
            print(f"[DADOS] Preço: R$ {dados['preco']:.2f}")
            print(f"[DADOS] LPA: R$ {dados['lpa']:.2f}")
            print(f"[DADOS] P/L: {dados['pl']:.2f}")
            print(f"[DADOS] ROE: {dados['roe']:.2f}%")
            print(f"[DADOS] DY: {dados['dy']:.2f}%")
            print(f"[DADOS] VPA: R$ {dados['vpa']:.2f}")
            
        except json.JSONDecodeError as e:
            print(f"[ERRO JSON] {e}")
            print(f"[RESPOSTA IA] {conteudo}")
            return None
        except Exception as e:
            print(f"[ERRO IA] {e}")
            import traceback
            traceback.print_exc()
            return None
        
        # Validar dados mínimos
        if dados['preco'] == 0 or dados['lpa'] == 0:
            print(f"[ERRO] Dados insuficientes: preço={dados['preco']}, lpa={dados['lpa']}")
            return None
        
        # Calcular P/L se não veio (mas temos preço e LPA)
        if dados['pl'] == 0 and dados['preco'] > 0 and dados['lpa'] > 0:
            dados['pl'] = dados['preco'] / dados['lpa']
            print(f"[CALC] P/L calculado: {dados['pl']:.2f}")
        
        print(f"[OK] ✅ Dados completos extraídos!")
        return dados
        
    except requests.Timeout:
        print(f"[ERRO] Timeout ao acessar {url}")
        return None
    except Exception as e:
        print(f"[ERRO] Extração: {e}")
        import traceback
        traceback.print_exc()
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
    - Web scraping + IA do Investidor10
    - 3 métodos (Bazin, Graham, Lynch)
    - Análise IA
    - Resumo de notícias
    """
    
    # 1. Extrair dados via web scraping + IA
    print(f"[VALUATION] Iniciando análise de {ticker}...")
    dados = extrair_dados_investidor10(ticker)
    
    if not dados:
        print(f"[VALUATION] ❌ Falha ao extrair dados")
        return None
    
    # 2. Gerar análise IA
    print(f"[VALUATION] Gerando análise IA...")
    ai_analysis = gerar_analise_ia(ticker, dados)
    
    # 3. Buscar notícias
    print(f"[VALUATION] Buscando notícias...")
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
    
    print(f"[VALUATION] ✅ Análise completa!")
    
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
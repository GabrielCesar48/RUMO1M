"""
Serviço de cálculo de valuation usando yfinance (Yahoo Finance)
Implementação das metodologias: Bazin, Graham e Lynch (PEG)
"""

import yfinance as yf
from decimal import Decimal


def obter_dados_acao(ticker: str):
    """
    Busca dados fundamentalistas via yfinance (Yahoo Finance)
    Retorna apenas dados reais disponíveis
    """
    try:
        ticker_limpo = ticker.strip().upper()
        if not ticker_limpo.endswith('.SA'):
            ticker_limpo = f"{ticker_limpo}.SA"
        
        print(f"[DEBUG] Buscando: {ticker_limpo}")
        
        # Buscar via yfinance
        stock = yf.Ticker(ticker_limpo)
        info = stock.info
        
        # Validar se retornou dados
        if not info or 'currentPrice' not in info:
            print(f"[ERRO] Dados não encontrados para {ticker_limpo}")
            return None
        
        # Extrair dados
        dados = {
            'ticker': ticker_limpo.replace('.SA', ''),
            'preco': 0,
            'eps': 0,
            'pe': 0,
            'roe': 0,
            'dy': 0,
            'vpa': 0,
        }
        
        # PREÇO
        dados['preco'] = float(info.get('currentPrice', 0) or info.get('regularMarketPrice', 0))
        
        # EPS (Earnings Per Share)
        eps_raw = info.get('trailingEps') or info.get('epsTrailingTwelveMonths')
        if eps_raw:
            dados['eps'] = abs(float(eps_raw))
        
        # P/L (Price to Earnings)
        pe_raw = info.get('trailingPE') or info.get('forwardPE')
        if pe_raw:
            dados['pe'] = abs(float(pe_raw))
        
        # ROE (Return on Equity) - já vem em decimal (0.15 = 15%)
        roe_raw = info.get('returnOnEquity')
        if roe_raw:
            dados['roe'] = abs(float(roe_raw) * 100)
        
        # DY (Dividend Yield) - já vem em decimal (0.05 = 5%)
        dy_raw = info.get('dividendYield') or info.get('trailingAnnualDividendYield')
        if dy_raw:
            dados['dy'] = abs(float(dy_raw) * 100)
        
        # VPA (Valor Patrimonial por Ação = Book Value)
        vpa_raw = info.get('bookValue')
        if vpa_raw:
            dados['vpa'] = abs(float(vpa_raw))
        
        # Calcular campos faltantes
        if dados['eps'] == 0 and dados['pe'] > 0 and dados['preco'] > 0:
            dados['eps'] = dados['preco'] / dados['pe']
            print(f"[INFO] EPS calculado: R$ {dados['eps']:.2f}")
        
        if dados['pe'] == 0 and dados['eps'] > 0 and dados['preco'] > 0:
            dados['pe'] = dados['preco'] / dados['eps']
            print(f"[INFO] P/L calculado: {dados['pe']:.2f}")
        
        # Validar mínimos
        if dados['preco'] == 0:
            print(f"[ERRO] Preço não encontrado")
            return None
        
        if dados['eps'] == 0:
            print(f"[ERRO] EPS não disponível")
            return None
        
        # Log final
        print(f"[OK] {ticker_limpo}:")
        print(f"    Preço: R$ {dados['preco']:.2f}")
        print(f"    EPS: R$ {dados['eps']:.2f}")
        print(f"    P/L: {dados['pe']:.2f}x")
        print(f"    ROE: {dados['roe']:.2f}%")
        print(f"    DY: {dados['dy']:.2f}%")
        print(f"    VPA: R$ {dados['vpa']:.2f}")
        
        return dados
        
    except Exception as e:
        print(f"[ERRO] {e}")
        import traceback
        traceback.print_exc()
        return None


def calcular_valuation(ticker: str):
    """
    Calcula valuation com 3 metodologias:
    1. BAZIN - Foco em dividendos
    2. GRAHAM - Value investing clássico  
    3. LYNCH - Crescimento (PEG Ratio)
    """
    dados = obter_dados_acao(ticker)
    
    if not dados:
        return None
    
    preco = Decimal(str(dados['preco']))
    eps = Decimal(str(dados['eps']))
    roe = Decimal(str(dados['roe']))
    pe = Decimal(str(dados['pe']))
    dy = Decimal(str(dados['dy']))
    vpa = Decimal(str(dados['vpa']))
    
    # ============================================================
    # MÉTODO BAZIN
    # Preço Teto = DPA / 0.06 (rentabilidade mínima 6% a.a.)
    # ============================================================
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
    
    # ============================================================
    # MÉTODO GRAHAM
    # Preço Justo = √(22.5 × EPS × VPA)
    # ============================================================
    graham_justo = None
    graham_status = "DADOS_INSUFICIENTES"
    graham_margem = None
    graham_formula = "Necessita EPS e VPA"
    
    if eps > 0 and vpa > 0:
        graham_justo = float((Decimal('22.5') * eps * vpa).sqrt())
        margem = ((Decimal(str(graham_justo)) - preco) / Decimal(str(graham_justo))) * 100
        
        if preco <= Decimal(str(graham_justo)) * Decimal('0.66'):
            graham_status = "COMPRAR"
        elif preco <= Decimal(str(graham_justo)):
            graham_status = "AGUARDAR"
        else:
            graham_status = "VENDER"
        
        graham_margem = float(margem)
        graham_formula = f"√(22.5 × R$ {float(eps):.2f} × R$ {float(vpa):.2f}) = R$ {graham_justo:.2f}"
    
    elif eps > 0:
        # Fallback: usar apenas P/L se não tiver VPA
        graham_justo = float(eps * 15)
        margem = ((Decimal(str(graham_justo)) - preco) / Decimal(str(graham_justo))) * 100
        
        if preco <= Decimal(str(graham_justo)) * Decimal('0.75'):
            graham_status = "COMPRAR"
        elif preco <= Decimal(str(graham_justo)):
            graham_status = "AGUARDAR"
        else:
            graham_status = "VENDER"
        
        graham_margem = float(margem)
        graham_formula = f"EPS (R$ {float(eps):.2f}) × 15 = R$ {graham_justo:.2f}"
    
    # ============================================================
    # MÉTODO LYNCH (PEG RATIO)
    # PEG = P/L / ROE
    # ============================================================
    lynch_peg = None
    lynch_status = "DADOS_INSUFICIENTES"
    lynch_margem = None
    lynch_ideal = None
    lynch_formula = "Necessita P/L e ROE"
    
    if pe > 0 and roe > 0:
        lynch_peg = float(pe / roe)
        lynch_ideal = float(eps * roe)
        
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
        
        lynch_formula = f"P/L ({float(pe):.2f}) ÷ ROE ({float(roe):.2f}%) = {lynch_peg:.2f}"
    
    # ============================================================
    # RECOMENDAÇÃO GERAL (Votação)
    # ============================================================
    metodos_validos = [s for s in [bazin_status, graham_status, lynch_status] 
                       if s != "DADOS_INSUFICIENTES"]
    
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
    
    return {
        'ticker': dados['ticker'],
        'preco_atual': f"R$ {float(preco):.2f}",
        
        'dados_base': {
            'preco': f"R$ {float(preco):.2f}",
            'eps': f"R$ {float(eps):.2f}",
            'pe': f"{float(pe):.2f}x",
            'roe': f"{float(roe):.2f}%" if roe > 0 else "N/A",
            'dy': f"{float(dy):.2f}%" if dy > 0 else "N/A",
        },
        
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
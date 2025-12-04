"""
Serviço de cálculo de valuation usando brapi.dev
VERSÃO FINAL - APENAS DADOS REAIS (sem estimativas)
"""

from decimal import Decimal
import requests

# TOKEN DA BRAPI.DEV
BRAPI_TOKEN = "pMMxagDigxKbDi8aQKWbrW"


def obter_dados_acao(ticker: str):
    """
    Busca dados fundamentalistas via brapi.dev
    RETORNA APENAS DADOS REAIS - Sem estimativas ou cálculos
    """
    try:
        ticker_limpo = ticker.strip().upper().rstrip('F')
        
        # Requisição completa com todos os módulos disponíveis
        url = f"https://brapi.dev/api/quote/{ticker_limpo}?token={BRAPI_TOKEN}&fundamental=true&modules=summaryProfile"
        
        print(f"[DEBUG] Buscando: {ticker_limpo}")
        resp = requests.get(url, timeout=10)
        
        if not resp.ok:
            print(f"[ERRO] API retornou status {resp.status_code}")
            return None
        
        data = resp.json()
        
        if 'results' not in data or len(data['results']) == 0:
            print(f"[ERRO] Nenhum resultado")
            return None
        
        stock = data['results'][0]
        
        # Preço
        preco = float(stock.get('regularMarketPrice', 0))
        if preco == 0:
            print(f"[ERRO] Preço não encontrado")
            return None
        
        dados = {
            'ticker': ticker_limpo,
            'preco': preco,
            'eps': 0,
            'pe': 0,
            'roe': 0,
            'dy': 0,
        }
        
        # EPS - Lucro Por Ação (múltiplas chaves possíveis)
        eps_raw = stock.get('earningsPerShare') or stock.get('epsTrailingTwelveMonths')
        if eps_raw:
            dados['eps'] = abs(float(eps_raw))
        
        # P/L - Preço / Lucro (múltiplas chaves possíveis)
        pe_raw = stock.get('priceEarnings') or stock.get('trailingPE')
        if pe_raw:
            dados['pe'] = abs(float(pe_raw))
        
        # ROE - Retorno sobre Patrimônio (APENAS DADOS REAIS)
        roe_raw = stock.get('returnOnEquity') or stock.get('roe')
        if roe_raw:
            roe_val = float(roe_raw)
            # Se vier em decimal (0.15 = 15%), multiplica por 100
            dados['roe'] = abs(roe_val * 100 if roe_val < 1 else roe_val)
        
        # DY - Dividend Yield (APENAS DADOS REAIS)
        dy_raw = (
            stock.get('dividendYield') or 
            stock.get('lastDividendYield') or
            stock.get('trailingAnnualDividendYield')
        )
        if dy_raw:
            dy_val = float(dy_raw)
            # Se vier em decimal (0.05 = 5%), multiplica por 100
            dados['dy'] = abs(dy_val * 100 if dy_val < 1 else dy_val)
        
        # Calcular EPS e P/L se um existir e o outro não
        if dados['eps'] == 0 and dados['pe'] > 0:
            dados['eps'] = preco / dados['pe']
            print(f"[INFO] EPS calculado via P/L: R$ {dados['eps']:.2f}")
        
        if dados['pe'] == 0 and dados['eps'] > 0:
            dados['pe'] = preco / dados['eps']
            print(f"[INFO] P/L calculado via EPS: {dados['pe']:.2f}")
        
        # Validar mínimos necessários
        if dados['eps'] == 0:
            print(f"[ERRO] EPS não disponível")
            return None
        
        # Log final
        print(f"[OK] {ticker_limpo}:")
        print(f"    Preço: R$ {dados['preco']:.2f}")
        print(f"    P/L: {dados['pe']:.2f}x")
        print(f"    EPS: R$ {dados['eps']:.2f}")
        print(f"    ROE: {dados['roe']:.2f}% {'(REAL)' if dados['roe'] > 0 else '(NÃO DISPONÍVEL)'}")
        print(f"    DY: {dados['dy']:.2f}% {'(REAL)' if dados['dy'] > 0 else '(NÃO DISPONÍVEL)'}")
        
        return dados
        
    except Exception as e:
        print(f"[ERRO] Exceção: {e}")
        import traceback
        traceback.print_exc()
        return None


def calcular_valuation(ticker: str):
    """
    Calcula valuation com 3 métodos: Bazin, Graham e Lynch (PEG)
    Só calcula se houver dados reais disponíveis
    """
    dados = obter_dados_acao(ticker)
    
    if not dados:
        return None
    
    preco = Decimal(str(dados['preco']))
    eps = Decimal(str(dados['eps']))
    roe = Decimal(str(dados['roe']))
    pe = Decimal(str(dados['pe']))
    dy = Decimal(str(dados['dy']))
    
    # ============================================================
    # MÉTODO BAZIN - Baseado em Dividend Yield de 6%
    # ============================================================
    bazin_teto = None
    bazin_status = "DADOS_INSUFICIENTES"
    bazin_margem = None
    bazin_formula = "Dividend Yield não disponível na API"
    
    if dy > 0:
        # Preço Teto = DPA / 0.06
        # DPA (Dividendo por Ação) = (DY / 100) * Preço
        dpa = (dy / 100) * preco
        bazin_teto = float(dpa / Decimal('0.06'))
        margem = (bazin_teto - float(preco)) / bazin_teto * 100
        
        # Critérios Bazin
        if float(preco) <= bazin_teto * 0.8:
            bazin_status = "COMPRAR"
        elif float(preco) <= bazin_teto:
            bazin_status = "COMPRAR"
        elif float(preco) <= bazin_teto * 1.05:
            bazin_status = "AGUARDAR"
        else:
            bazin_status = "VENDER"
        
        bazin_margem = margem
        bazin_formula = f"DPA (R$ {float(dpa):.2f}) ÷ 0.06 = R$ {bazin_teto:.2f}"
    
    # ============================================================
    # MÉTODO GRAHAM - Preço Justo com P/L 15x
    # ============================================================
    graham_justo = None
    graham_status = "DADOS_INSUFICIENTES"
    graham_margem = None
    graham_formula = "EPS não disponível"
    
    if eps > 0:
        graham_justo = float(eps * 15)
        margem = (graham_justo - float(preco)) / graham_justo * 100
        
        # Critérios Graham
        if float(preco) <= graham_justo * 0.75:
            graham_status = "COMPRAR"
        elif float(preco) < graham_justo:
            graham_status = "COMPRAR"
        elif float(preco) <= graham_justo * 1.05:
            graham_status = "AGUARDAR"
        else:
            graham_status = "VENDER"
        
        graham_margem = margem
        graham_formula = f"EPS (R$ {float(eps):.2f}) × 15 = R$ {graham_justo:.2f}"
    
    # ============================================================
    # MÉTODO LYNCH - PEG Ratio (APENAS SE HOUVER ROE REAL)
    # ============================================================
    lynch_peg = None
    lynch_status = "DADOS_INSUFICIENTES"
    lynch_margem = None
    lynch_ideal = None
    lynch_formula = "ROE não disponível na API"
    
    if roe > 0 and pe > 0:
        lynch_peg = float(pe / roe)
        lynch_ideal = float(eps * roe)
        
        if lynch_ideal > 0:
            margem = (lynch_ideal - float(preco)) / lynch_ideal * 100
            lynch_margem = margem
        
        # Critérios PEG
        if lynch_peg < 0.8:
            lynch_status = "COMPRAR"
        elif lynch_peg <= 1.0:
            lynch_status = "COMPRAR"
        elif lynch_peg <= 1.5:
            lynch_status = "AGUARDAR"
        elif lynch_peg <= 2.0:
            lynch_status = "AGUARDAR"
        else:
            lynch_status = "VENDER"
        
        lynch_formula = f"P/L ({float(pe):.2f}) ÷ ROE ({float(roe):.2f}%) = {lynch_peg:.2f}"
    
    # ============================================================
    # RECOMENDAÇÃO GERAL (VOTAÇÃO - só conta métodos com dados)
    # ============================================================
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
    
    # ============================================================
    # RETORNAR RESULTADO ESTRUTURADO
    # ============================================================
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
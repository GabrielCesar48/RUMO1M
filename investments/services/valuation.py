"""
Serviço de cálculo de valuation - VERSÃO SIMPLIFICADA
Sem classes complexas, direto ao ponto.
"""

from decimal import Decimal
import requests


def obter_dados_acao(ticker: str):
    """Busca dados da ação via brapi.dev"""
    try:
        ticker_limpo = ticker.strip().upper().rstrip('F')
        url = f"https://brapi.dev/api/quote/{ticker_limpo}"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 404 or not response.ok:
            return None
        
        data = response.json()
        if 'results' not in data or len(data['results']) == 0:
            return None
        
        stock = data['results'][0]
        
        # Extrair dados com fallback
        return {
            'ticker': ticker_limpo,
            'preco': float(stock.get('regularMarketPrice', 0)) or 0,
            'pe': float(stock.get('trailingPE', 0)) or 15,
            'eps': float(stock.get('trailingEps', 0)) or 0,
            'roe': (float(stock.get('returnOnEquity', 0)) or 0) * 100,
            'dy': (float(stock.get('dividendYield', 0)) or 0) * 100,
        }
    except Exception as e:
        print(f"[ERRO] Buscar dados: {e}")
        return None


def calcular_valuation(ticker: str):
    """
    Calcula valuation com 3 métodos: Bazin, Graham, Lynch
    Retorna dict com todos os cálculos
    """
    # Buscar dados
    dados = obter_dados_acao(ticker)
    if not dados:
        return None
    
    preco = Decimal(str(dados['preco']))
    eps = Decimal(str(dados['eps']))
    roe = Decimal(str(dados['roe']))
    pe = Decimal(str(dados['pe']))
    
    # ========== BAZIN: Preço-teto ==========
    bazin_teto = None
    bazin_status = "DADOS_INSUFICIENTES"
    bazin_margem = None
    
    if eps > 0:
        bazin_teto = float(eps / Decimal('0.06'))
        margem = (bazin_teto - float(preco)) / bazin_teto * 100
        
        if float(preco) < bazin_teto * 0.8:
            bazin_status = "COMPRAR"
        elif float(preco) <= bazin_teto:
            bazin_status = "COMPRAR"
        elif float(preco) <= bazin_teto * 1.05:
            bazin_status = "AGUARDAR"
        else:
            bazin_status = "VENDER"
        
        bazin_margem = margem
    
    # ========== GRAHAM: Preço Justo ==========
    graham_justo = None
    graham_status = "DADOS_INSUFICIENTES"
    graham_margem = None
    
    if eps > 0:
        graham_justo = float(eps * 15)
        margem = (graham_justo - float(preco)) / graham_justo * 100
        
        if float(preco) < graham_justo * 0.75:
            graham_status = "COMPRAR"
        elif float(preco) < graham_justo:
            graham_status = "COMPRAR"
        elif float(preco) <= graham_justo * 1.05:
            graham_status = "AGUARDAR"
        else:
            graham_status = "VENDER"
        
        graham_margem = margem
    
    # ========== LYNCH: PEG Ratio ==========
    lynch_peg = None
    lynch_status = "DADOS_INSUFICIENTES"
    lynch_margem = None
    lynch_ideal = None
    
    if roe > 0 and pe > 0:
        lynch_peg = float(pe / roe)
        lynch_ideal = float(eps * roe)
        
        if lynch_ideal > 0:
            margem = (lynch_ideal - float(preco)) / lynch_ideal * 100
            lynch_margem = margem
        
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
    
    # ========== VOTAÇÃO ==========
    votos_compra = sum([1 for s in [bazin_status, graham_status, lynch_status] 
                        if s == "COMPRAR"])
    votos_venda = sum([1 for s in [bazin_status, graham_status, lynch_status] 
                       if s == "VENDER"])
    
    if votos_compra >= 2:
        status_geral = "COMPRAR"
    elif votos_venda >= 2:
        status_geral = "VENDER"
    else:
        status_geral = "AGUARDAR"
    
    # ========== FORMATAR RESULTADO ==========
    return {
        'ticker': dados['ticker'],
        'preco_atual': f"R$ {float(preco):.2f}",
        'preco_atual_raw': float(preco),
        
        'bazin': {
            'preco_teto': f"R$ {bazin_teto:.2f}" if bazin_teto else "N/A",
            'preco_teto_raw': bazin_teto,
            'status': bazin_status,
            'margem': f"{bazin_margem:.1f}%" if bazin_margem is not None else "N/A",
            'margem_raw': bazin_margem,
            'emoji': '🟢' if bazin_status == 'COMPRAR' else ('🔴' if bazin_status == 'VENDER' else '🟡'),
        },
        
        'graham': {
            'preco_justo': f"R$ {graham_justo:.2f}" if graham_justo else "N/A",
            'preco_justo_raw': graham_justo,
            'status': graham_status,
            'margem': f"{graham_margem:.1f}%" if graham_margem is not None else "N/A",
            'margem_raw': graham_margem,
            'emoji': '🟢' if graham_status == 'COMPRAR' else ('🔴' if graham_status == 'VENDER' else '🟡'),
        },
        
        'lynch': {
            'peg': f"{lynch_peg:.2f}" if lynch_peg else "N/A",
            'peg_raw': lynch_peg,
            'preco_ideal': f"R$ {lynch_ideal:.2f}" if lynch_ideal else "N/A",
            'preco_ideal_raw': lynch_ideal,
            'status': lynch_status,
            'margem': f"{lynch_margem:.1f}%" if lynch_margem is not None else "N/A",
            'margem_raw': lynch_margem,
            'emoji': '🟢' if lynch_status == 'COMPRAR' else ('🔴' if lynch_status == 'VENDER' else '🟡'),
        },
        
        'recomendacao': {
            'status': status_geral,
            'emoji': '🟢' if status_geral == 'COMPRAR' else ('🔴' if status_geral == 'VENDER' else '🟡'),
            'pontos_compra': votos_compra,
            'pontos_venda': votos_venda,
        }
    }
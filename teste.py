"""
TESTE: Verificar se yfinance funciona na sua máquina

Execute este arquivo para testar:
python teste_yfinance.py
"""

import yfinance as yf

print("=" * 60)
print("TESTE: yfinance - Yahoo Finance")
print("=" * 60)

try:
    print("\n1. Testando PETR4.SA...")
    ticker = yf.Ticker('PETR4.SA')
    info = ticker.info
    
    if info and 'currentPrice' in info:
        print(f"✅ SUCESSO!")
        print(f"   Nome: {info.get('longName', 'N/A')}")
        print(f"   Preço: R$ {info.get('currentPrice', 0):.2f}")
        print(f"   P/L: {info.get('trailingPE', 0):.2f}")
        print(f"   EPS: R$ {info.get('trailingEps', 0):.2f}")
        
        roe = info.get('returnOnEquity')
        if roe:
            print(f"   ROE: {roe * 100:.2f}%")
        else:
            print(f"   ROE: N/A")
        
        dy = info.get('dividendYield')
        if dy:
            print(f"   DY: {dy * 100:.2f}%")
        else:
            print(f"   DY: N/A")
        
        print(f"   Book Value: R$ {info.get('bookValue', 0):.2f}")
        
        print("\n✅ yfinance está FUNCIONANDO!")
        print("✅ Pode usar os arquivos com yfinance no seu projeto.")
        
    else:
        print("❌ FALHOU: Não retornou dados")
        print("❌ Possível problema de conexão ou ticker inválido")

except Exception as e:
    print(f"❌ ERRO: {e}")
    print("\nPossíveis causas:")
    print("1. Sem conexão com internet")
    print("2. Firewall bloqueando acesso ao Yahoo Finance")
    print("3. yfinance não instalado: pip install yfinance")

print("\n" + "=" * 60)
print("\n2. Testando mais ações...")

acoes_teste = ['VALE3.SA', 'BBAS3.SA', 'ITUB4.SA']

for acao in acoes_teste:
    try:
        print(f"\n   Testando {acao}...", end=" ")
        t = yf.Ticker(acao)
        preco = t.info.get('currentPrice', 0)
        if preco > 0:
            print(f"✅ R$ {preco:.2f}")
        else:
            print(f"⚠️ Sem preço")
    except:
        print(f"❌ Erro")

print("\n" + "=" * 60)
print("FIM DO TESTE")
print("=" * 60)
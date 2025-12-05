"""
TESTE SIMPLES: Valuation com Web Scraping Real

Execute: python teste_scraping.py
"""

import os
from decouple import config

os.environ['OPENAI_API_KEY'] = config('OPENAI_API_KEY')

# Importar do novo módulo
from investments.services.valuation_openai import calcular_valuation

print("=" * 60)
print("TESTE: Valuation com Web Scraping Real")
print("=" * 60)

# Testar com VALE3
ticker = 'VALE3'
print(f"\n🔍 Testando: {ticker}")
print("-" * 60)

resultado = calcular_valuation(ticker)

if resultado:
    print("\n✅ SUCESSO! Dados extraídos:\n")
    
    print("📊 DADOS BASE:")
    for chave, valor in resultado['dados_base'].items():
        print(f"   {chave}: {valor}")
    
    print(f"\n🎯 RECOMENDAÇÃO GERAL:")
    print(f"   {resultado['recomendacao']['emoji']} {resultado['recomendacao']['status']}")
    print(f"   Votos COMPRAR: {resultado['recomendacao']['pontos_compra']}")
    print(f"   Votos VENDER: {resultado['recomendacao']['pontos_venda']}")
    
else:
    print("\n❌ FALHOU: Não foi possível extrair dados")

print("\n" + "=" * 60)
print("FIM DO TESTE")
print("=" * 60)
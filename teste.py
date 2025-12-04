"""
TESTE: Valuation com OpenAI + Investidor10

Execute este arquivo para testar:
python teste_openai_valuation.py
"""

import os
from decouple import config

os.environ['OPENAI_API_KEY'] =config('OPENAI_API_KEY')

from investments.services.valuation_openai import calcular_valuation

print("=" * 60)
print("TESTE: Valuation com OpenAI + Investidor10")
print("=" * 60)

# Testar com PETR4
ticker = 'PETR4'
print(f"\n🔍 Testando: {ticker}")
print("-" * 60)

resultado = calcular_valuation(ticker)

if resultado:
    print("\n✅ SUCESSO! Dados extraídos:\n")
    
    print("📊 DADOS BASE:")
    for chave, valor in resultado['dados_base'].items():
        print(f"   {chave}: {valor}")
    
    print("\n💰 MÉTODO BAZIN:")
    print(f"   Preço Teto: {resultado['bazin']['preco_teto']}")
    print(f"   Status: {resultado['bazin']['emoji']} {resultado['bazin']['status']}")
    print(f"   Margem: {resultado['bazin']['margem']}")
    print(f"   Fórmula: {resultado['bazin']['formula']}")
    
    print("\n📈 MÉTODO GRAHAM:")
    print(f"   Preço Justo: {resultado['graham']['preco_justo']}")
    print(f"   Status: {resultado['graham']['emoji']} {resultado['graham']['status']}")
    print(f"   Margem: {resultado['graham']['margem']}")
    print(f"   Fórmula: {resultado['graham']['formula']}")
    
    print("\n🚀 MÉTODO LYNCH:")
    print(f"   PEG: {resultado['lynch']['peg']}")
    print(f"   Preço Ideal: {resultado['lynch']['preco_ideal']}")
    print(f"   Status: {resultado['lynch']['emoji']} {resultado['lynch']['status']}")
    print(f"   Margem: {resultado['lynch']['margem']}")
    print(f"   Fórmula: {resultado['lynch']['formula']}")
    
    print("\n🎯 RECOMENDAÇÃO GERAL:")
    print(f"   {resultado['recomendacao']['emoji']} {resultado['recomendacao']['status']}")
    print(f"   Votos COMPRAR: {resultado['recomendacao']['pontos_compra']}")
    print(f"   Votos VENDER: {resultado['recomendacao']['pontos_venda']}")
    
else:
    print("\n❌ FALHOU: Não foi possível extrair dados")

print("\n" + "=" * 60)
print("\n🧪 Testando mais ações...")

acoes_teste = ['VALE3', 'BBAS3', 'ITUB4']

for acao in acoes_teste:
    print(f"\n   Testando {acao}...", end=" ")
    resultado = calcular_valuation(acao)
    if resultado:
        print(f"✅ {resultado['recomendacao']['emoji']} {resultado['recomendacao']['status']}")
    else:
        print(f"❌ Falhou")

print("\n" + "=" * 60)
print("FIM DO TESTE")
print("=" * 60)
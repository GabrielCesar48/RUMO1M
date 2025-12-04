from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Aporte, Lancamento
from .forms import AporteForm
import requests
from decimal import Decimal
from django.views.decorators.http import require_http_methods

@login_required
def adicionar_aporte(request):
    # Buscar o próximo valor sugerido (mesma lógica do dashboard)
    aportes = Aporte.objects.filter(usuario=request.user).order_by("data")
    
    proximo_valor = None
    if aportes.exists():
        from investments.services.inflacao import calcular_proximo_aporte
        proximo_sugerido = calcular_proximo_aporte(aportes)
        proximo_valor = proximo_sugerido if proximo_sugerido else 0
    else:
        proximo_valor = 0
    
    if request.method == 'POST':
        form = AporteForm(request.POST)
        if form.is_valid():
            aporte = form.save(commit=False)
            aporte.usuario = request.user
            aporte.save()
            messages.success(request, f'Aporte de R$ {aporte.valor} adicionado! 🎉')
            return redirect('dashboard')
    else:
        form = AporteForm()
    
    return render(request, 'investments/adicionar.html', {
        'form': form,
        'proximo_valor': proximo_valor
    })

@login_required
def editar_aporte(request, pk):
    aporte = get_object_or_404(Aporte, pk=pk, usuario=request.user)
    
    if request.method == 'POST':
        form = AporteForm(request.POST, instance=aporte)
        if form.is_valid():
            form.save()
            messages.success(request, 'Aporte atualizado!')
            return redirect('dashboard')
    else:
        form = AporteForm(instance=aporte)
    
    return render(request, 'investments/editar.html', {'form': form, 'aporte': aporte})

@login_required
def deletar_aporte(request, pk):
    aporte = get_object_or_404(Aporte, pk=pk, usuario=request.user)
    
    if request.method == 'POST':
        valor = aporte.valor
        aporte.delete()
        messages.success(request, f'Aporte de R$ {valor} removido!')
        return redirect('dashboard')
    
    return render(request, 'investments/deletar.html', {'aporte': aporte})

@login_required
def buscar_ativos_api(request):
    """Busca ativos via brapi.dev"""
    query = request.GET.get('q', '').strip()
    tipo_ativo = request.GET.get('tipo', 'ACOES')
    
    if len(query) < 2:
        return JsonResponse({'resultados': []})
    
    try:
        # API brapi.dev
        url = f"https://brapi.dev/api/quote/list?search={query}&limit=10"
        response = requests.get(url, timeout=5)
        data = response.json()
        
        resultados = []
        if 'stocks' in data:
            for stock in data['stocks']:
                # Filtrar por tipo se necessário
                resultados.append({
                    'ticker': stock.get('stock'),
                    'nome': stock.get('name'),
                    'tipo': stock.get('type', 'stock')
                })
        
        return JsonResponse({'resultados': resultados})
    except Exception as e:
        return JsonResponse({'erro': str(e)}, status=500)

@login_required
def buscar_cotacao_api(request):
    """Busca cotação atual via brapi.dev"""
    ticker = request.GET.get('ticker', '').strip().upper()
    
    if not ticker:
        return JsonResponse({'erro': 'Ticker não informado'}, status=400)
    
    try:
        # Tentar com o ticker original
        url = f"https://brapi.dev/api/quote/{ticker}?token=wWnUUimgEEC3uu8dXsdrTa"
        response = requests.get(url, timeout=5)
        
        # Se der 404, pode ser que o ticker tenha sufixo
        if response.status_code == 404:
            # Tenta sem sufixo (ex: PETR3F -> PETR3)
            ticker_limpo = ticker.rstrip('F')
            url = f"https://brapi.dev/api/quote/{ticker_limpo}?token=wWnUUimgEEC3uu8dXsdrTa"
            response = requests.get(url, timeout=5)
        
        if response.status_code == 404:
            return JsonResponse({
                'erro': 'Ativo não encontrado na API',
                'ticker': ticker,
                'preco': 0
            }, status=404)
        
        data = response.json()
        
        if 'results' in data and len(data['results']) > 0:
            resultado = data['results'][0]
            return JsonResponse({
                'ticker': resultado.get('symbol'),
                'nome': resultado.get('longName'),
                'preco': resultado.get('regularMarketPrice', 0),
                'moeda': resultado.get('currency', 'BRL')
            })
        else:
            return JsonResponse({
                'erro': 'Dados não disponíveis',
                'ticker': ticker,
                'preco': 0
            }, status=404)
    except requests.Timeout:
        return JsonResponse({'erro': 'Timeout na API', 'preco': 0}, status=500)
    except Exception as e:
        return JsonResponse({'erro': str(e), 'preco': 0}, status=500)

@login_required
def salvar_lancamentos(request):
    """Salva múltiplos lançamentos de uma vez"""
    if request.method != 'POST':
        return JsonResponse({'erro': 'Método não permitido'}, status=405)
    
    import json
    try:
        dados = json.loads(request.body)
        lancamentos_data = dados.get('lancamentos', [])
        
        lancamentos_salvos = []
        for lanc in lancamentos_data:
            # Tratar taxa_cdi
            indexador = lanc.get('indexador', '')
            taxa_cdi = lanc.get('taxa_cdi', 0)
            
            if indexador == 'CDI' and taxa_cdi:
                indexador = f"CDI {taxa_cdi}%"
            
            # Converter data_vencimento vazia para None
            data_vencimento = lanc.get('data_vencimento')
            if data_vencimento == '' or data_vencimento is None:
                data_vencimento = None
            
            lancamento = Lancamento.objects.create(
                usuario=request.user,
                tipo_operacao=lanc['tipo_operacao'],
                tipo_ativo=lanc['tipo_ativo'],
                ticker=lanc.get('ticker', ''),
                nome_ativo=lanc['nome_ativo'],
                data=lanc['data'],
                quantidade=Decimal(str(lanc['quantidade'])),
                preco=Decimal(str(lanc['preco'])),
                custos=Decimal(str(lanc.get('custos', 0))),
                total=Decimal(str(lanc['total'])),
                emissor=lanc.get('emissor', ''),
                tipo_renda_fixa=lanc.get('tipo_renda_fixa', ''),
                indexador=indexador,
                data_vencimento=data_vencimento,
                liquidez_diaria=lanc.get('liquidez_diaria', False)
            )
            lancamentos_salvos.append(lancamento.id)
        
        messages.success(request, f'{len(lancamentos_salvos)} lançamento(s) adicionado(s)! 🎉')
        return JsonResponse({
            'sucesso': True,
            'quantidade': len(lancamentos_salvos),
            'ids': lancamentos_salvos
        })
    except Exception as e:
        return JsonResponse({'erro': str(e)}, status=500)
    
def consolidar_carteira(usuario):
    """Consolida todas as operações em posições atuais"""
    from collections import defaultdict
    
    lancamentos = Lancamento.objects.filter(usuario=usuario).order_by('data')
    
    # Agrupar por ticker/nome
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
            # Compra: adiciona quantidade
            qtd_anterior = posicoes[chave]['quantidade']
            valor_anterior = posicoes[chave]['valor_total']
            
            posicoes[chave]['quantidade'] += lanc.quantidade
            posicoes[chave]['valor_total'] += lanc.total
            posicoes[chave]['valor_medio'] = posicoes[chave]['valor_total'] / posicoes[chave]['quantidade'] if posicoes[chave]['quantidade'] > 0 else Decimal('0')
        else:
            # Venda: remove quantidade
            posicoes[chave]['quantidade'] -= lanc.quantidade
            # Reduz valor proporcional
            if posicoes[chave]['quantidade'] > 0:
                posicoes[chave]['valor_total'] = posicoes[chave]['valor_medio'] * posicoes[chave]['quantidade']
            else:
                posicoes[chave]['valor_total'] = Decimal('0')
        
        # Atualizar metadados
        posicoes[chave]['tipo_ativo'] = lanc.tipo_ativo
        posicoes[chave]['ticker'] = lanc.ticker
        posicoes[chave]['nome'] = lanc.nome_ativo
    
    # Buscar logos e preços atuais
    for chave, pos in posicoes.items():
        if pos['quantidade'] > 0 and pos['ticker']:
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
            except:
                pass
    
    # Filtrar apenas posições com quantidade > 0
    return {k: v for k, v in posicoes.items() if v['quantidade'] > 0}

@login_required
@require_http_methods(["GET"])
def buscar_acoes_valuation_api(request):
    """API para autocomplete de ações (valuation)"""
    query = request.GET.get('q', '').strip().upper()
    
    if len(query) < 1:
        return JsonResponse({'resultados': []})
    
    try:
        url = f"https://brapi.dev/api/quote/list?search={query}&limit=15"
        response = requests.get(url, timeout=5)
        
        if not response.ok:
            return JsonResponse({'resultados': []})
        
        data = response.json()
        resultados = []
        
        for stock in data.get('stocks', [])[:15]:
            ticker = stock.get('stock', '')
            nome = stock.get('name', '')[:50]
            
            resultados.append({
                'ticker': ticker,
                'nome': nome,
                'label': f"{ticker} - {nome}"
            })
        
        return JsonResponse({'resultados': resultados})
        
    except Exception as e:
        return JsonResponse({'resultados': []})


@login_required
@require_http_methods(["GET"])
def calcular_valuation_api(request):
    """API para calcular valuation de uma ação"""
    from investments.services.valuation import calcular_valuation
    
    ticker = request.GET.get('ticker', '').strip().upper()
    
    if not ticker:
        return JsonResponse({'erro': 'Ticker não informado'}, status=400)
    
    try:
        resultado = calcular_valuation(ticker)
        
        if not resultado:
            return JsonResponse({
                'erro': 'Ação não encontrada ou dados insuficientes',
                'ticker': ticker
            }, status=404)
        
        return JsonResponse({'resultado': resultado})
        
    except Exception as e:
        print(f"[ERRO] Calcular valuation: {e}")
        return JsonResponse({'erro': str(e)}, status=500)


@login_required
def valuation_page(request):
    """Página principal de análise de valuation"""
    return render(request, 'investments/valuation.html', {
        'page_title': 'Análise de Valuation'
    })
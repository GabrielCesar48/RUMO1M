from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Aporte, Lancamento, PlanejamentoMensal
from .forms import AporteForm
from decimal import Decimal
from django.views.decorators.http import require_http_methods
import requests


@login_required
def adicionar_aporte(request):
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
def editar_lancamento(request, pk):
    """Editar lançamento existente"""
    lancamento = get_object_or_404(Lancamento, pk=pk, usuario=request.user)
    
    if request.method == 'POST':
        try:
            lancamento.quantidade = Decimal(str(request.POST.get('quantidade', 0)))
            lancamento.preco = Decimal(str(request.POST.get('preco', 0)))
            lancamento.custos = Decimal(str(request.POST.get('custos', 0)))
            lancamento.total = (lancamento.quantidade * lancamento.preco) + lancamento.custos
            lancamento.data = request.POST.get('data')
            lancamento.nome_ativo = request.POST.get('nome_ativo', lancamento.nome_ativo)
            lancamento.save()
            messages.success(request, 'Lançamento atualizado! ✅')
            return redirect('dashboard')
        except Exception as e:
            messages.error(request, f'Erro ao atualizar: {str(e)}')
    
    return render(request, 'investments/editar_lancamento.html', {
        'lancamento': lancamento
    })


@login_required
def deletar_lancamento(request, pk):
    """Deletar lançamento"""
    lancamento = get_object_or_404(Lancamento, pk=pk, usuario=request.user)
    
    if request.method == 'POST':
        nome = lancamento.nome_ativo
        lancamento.delete()
        messages.success(request, f'Lançamento "{nome}" removido! 🗑️')
        return redirect('dashboard')
    
    return render(request, 'investments/deletar_lancamento.html', {
        'lancamento': lancamento
    })


@login_required
def buscar_ativos_api(request):
    """
    Busca ativos APENAS na API brapi.dev (suporta Ações e FIIs)
    Se API falhar, retorna vazio - sem fallback
    """
    query = request.GET.get('q', '').strip().upper()
    
    if len(query) < 2:
        return JsonResponse({'resultados': []})
    
    try:
        url = f"https://brapi.dev/api/quote/list?search={query}"
        response = requests.get(url, timeout=3)
        
        if response.ok:
            data = response.json()
            stocks = data.get('stocks', [])
            
            resultados = []
            for stock in stocks[:15]:
                ticker = stock.get('stock', '')
                nome = stock.get('name', ticker)
                
                # FIIs terminam em 11 (HGLG11, MXRF11)
                # Ações terminam em 3, 4, 5, 6 (PETR3, VALE3)
                tipo = 'fii' if ticker.endswith('11') else 'stock'
                
                resultados.append({
                    'ticker': ticker,
                    'nome': nome,
                    'tipo': tipo
                })
            
            return JsonResponse({'resultados': resultados})
    
    except Exception as e:
        print(f"[ERRO] Busca API: {e}")
    
    # Se API falhar, retorna vazio
    return JsonResponse({'resultados': []})


@login_required
def buscar_cotacao_api(request):
    """
    Busca cotação via yfinance
    
    ENSINO: Por que yfinance e não brapi.dev?
    - yfinance é mais confiável para cotações em tempo real
    - Suporta tanto ações quanto FIIs
    - Fallback automático se cotação não disponível
    """
    import yfinance as yf
    
    ticker = request.GET.get('ticker', '').strip().upper()
    
    if not ticker:
        return JsonResponse({'erro': 'Ticker não informado'}, status=400)
    
    try:
        # Adicionar sufixo .SA se não tiver
        if not ticker.endswith('.SA'):
            ticker = f"{ticker}.SA"
        
        stock = yf.Ticker(ticker)
        info = stock.info
        
        if 'currentPrice' in info:
            return JsonResponse({
                'ticker': ticker.replace('.SA', ''),
                'nome': info.get('longName', ''),
                'preco': float(info.get('currentPrice', 0) or info.get('regularMarketPrice', 0)),
                'moeda': 'BRL'
            })
        else:
            return JsonResponse({
                'erro': 'Dados não disponíveis',
                'ticker': ticker,
                'preco': 0
            }, status=404)
            
    except Exception as e:
        print(f"[ERRO] Buscar cotação: {e}")
        return JsonResponse({'erro': str(e), 'preco': 0}, status=500)


@login_required
def salvar_lancamentos(request):
    """Salva múltiplos lançamentos"""
    if request.method != 'POST':
        return JsonResponse({'erro': 'Método não permitido'}, status=405)
    
    import json
    try:
        dados = json.loads(request.body)
        lancamentos_data = dados.get('lancamentos', [])
        
        lancamentos_salvos = []
        for lanc in lancamentos_data:
            indexador = lanc.get('indexador', '')
            taxa_cdi = lanc.get('taxa_cdi', 0)
            
            if indexador == 'CDI' and taxa_cdi:
                indexador = f"CDI {taxa_cdi}%"
            
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
        print(f"[ERRO] Salvar lançamentos: {e}")
        return JsonResponse({'erro': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def buscar_acoes_valuation_api(request):
    """
    API para autocomplete na página de valuation
    Busca APENAS na API - sem fallback
    """
    query = request.GET.get('q', '').strip().upper()
    
    if len(query) < 1:
        return JsonResponse({'resultados': []})
    
    try:
        url = f"https://brapi.dev/api/quote/list?search={query}"
        response = requests.get(url, timeout=3)
        
        if response.ok:
            data = response.json()
            stocks = data.get('stocks', [])
            
            resultados = []
            for stock in stocks[:15]:
                ticker = stock.get('stock', '')
                nome = stock.get('name', ticker)
                
                # Para valuation, filtrar apenas ações (não FIIs)
                if not ticker.endswith('11'):
                    resultados.append({
                        'ticker': ticker,
                        'nome': nome,
                        'label': f"{ticker} - {nome}"
                    })
            
            return JsonResponse({'resultados': resultados})
    
    except Exception as e:
        print(f"[ERRO] Busca valuation: {e}")
    
    # Se API falhar, retorna vazio
    return JsonResponse({'resultados': []})


@login_required
@require_http_methods(["GET"])
def calcular_valuation_api(request):
    """
    API para calcular valuation usando OpenAI + Investidor10
    IMPORTANTE: Importa da versão correta (valuation_openai.py)
    """
    ticker = request.GET.get('ticker', '').strip().upper().replace('.SA', '')
    
    if not ticker:
        return JsonResponse({'erro': 'Ticker não informado'}, status=400)
    
    try:
        print(f"[API] Calculando valuation de {ticker}...")
        
        # ✅ IMPORTAÇÃO CORRETA - Mesma que funciona no teste.py
        from investments.services.valuation_openai import calcular_valuation
        
        # Chamar função que usa OpenAI + Web Scraping
        resultado = calcular_valuation(ticker)
        
        if not resultado:
            return JsonResponse({
                'erro': 'Não foi possível extrair dados do Investidor10 para esta ação',
                'ticker': ticker,
                'detalhes': 'A IA não conseguiu extrair os dados fundamentalistas do site'
            }, status=404)
        
        print(f"[API] ✅ Valuation calculado com sucesso para {ticker}")
        return JsonResponse({'resultado': resultado})
        
    except ImportError as e:
        print(f"[ERRO IMPORT] {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'erro': 'Erro ao importar módulo de valuation',
            'detalhes': str(e)
        }, status=500)
        
    except Exception as e:
        print(f"[ERRO] Calcular valuation: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'erro': 'Erro ao calcular valuation',
            'detalhes': str(e),
            'tipo_erro': type(e).__name__
        }, status=500)


@login_required
def valuation_page(request):
    """Página de análise de valuation"""
    return render(request, 'investments/valuation.html', {
        'page_title': 'Análise de Valuation'
    })


@login_required
def configurar_planejamento(request):
    """Criar ou editar planejamento mensal"""
    try:
        planejamento = PlanejamentoMensal.objects.get(usuario=request.user)
    except PlanejamentoMensal.DoesNotExist:
        planejamento = None
    
    if request.method == 'POST':
        valor_planejado = request.POST.get('valor_planejado', '').strip()
        
        if valor_planejado:
            try:
                valor_decimal = Decimal(valor_planejado.replace(',', '.'))
                
                if planejamento:
                    # Atualizar existente
                    planejamento.valor_planejado = valor_decimal
                    planejamento.save()
                    messages.success(request, 'Planejamento atualizado com sucesso! ✅')
                else:
                    # Criar novo
                    PlanejamentoMensal.objects.create(
                        usuario=request.user,
                        valor_planejado=valor_decimal
                    )
                    messages.success(request, 'Planejamento criado com sucesso! 🎉')
                
                return redirect('dashboard')
            except Exception as e:
                messages.error(request, f'Valor inválido. Use formato 500.00')
        else:
            messages.error(request, 'Por favor, informe o valor planejado.')
    
    # Calcular valor corrigido se existir planejamento
    valor_corrigido = None
    if planejamento:
        valor_corrigido = planejamento.calcular_valor_corrigido()
    
    return render(request, 'investments/planejamento.html', {
        'planejamento': planejamento,
        'valor_corrigido': valor_corrigido
    })
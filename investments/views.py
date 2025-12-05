from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Aporte, Lancamento, PlanejamentoMensal
from .forms import AporteForm
from decimal import Decimal
from django.views.decorators.http import require_http_methods


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
    """Busca ativos - LISTA ESTÁTICA (sem necessidade de API externa)"""
    query = request.GET.get('q', '').strip().upper()
    tipo_ativo = request.GET.get('tipo', 'ACOES')
    
    if len(query) < 2:
        return JsonResponse({'resultados': []})
    
    # Lista estática das principais ações brasileiras
    acoes_brasileiras = [
        ('PETR3', 'Petrobras ON'),
        ('PETR4', 'Petrobras PN'),
        ('VALE3', 'Vale ON'),
        ('ITUB3', 'Itaú Unibanco ON'),
        ('ITUB4', 'Itaú Unibanco PN'),
        ('BBDC3', 'Bradesco ON'),
        ('BBDC4', 'Bradesco PN'),
        ('BBAS3', 'Banco do Brasil ON'),
        ('ABEV3', 'Ambev ON'),
        ('B3SA3', 'B3 ON'),
        ('WEGE3', 'WEG ON'),
        ('RENT3', 'Localiza ON'),
        ('RAIL3', 'Rumo ON'),
        ('SUZB3', 'Suzano ON'),
        ('JBSS3', 'JBS ON'),
        ('MGLU3', 'Magazine Luiza ON'),
        ('LREN3', 'Lojas Renner ON'),
        ('GGBR4', 'Gerdau PN'),
        ('USIM5', 'Usiminas PNA'),
        ('CSNA3', 'CSN ON'),
        ('EMBR3', 'Embraer ON'),
        ('RADL3', 'Raia Drogasil ON'),
        ('HAPV3', 'Hapvida ON'),
        ('VIVT3', 'Telefônica Brasil ON'),
        ('ELET3', 'Eletrobras ON'),
        ('ELET6', 'Eletrobras PNB'),
        ('CMIG4', 'Cemig PN'),
        ('ENBR3', 'Energias BR ON'),
        ('ENGI11', 'Energisa UNT'),
        ('TAEE11', 'Taesa UNT'),
        ('CPLE6', 'Copel PNB'),
        ('SANB11', 'Santander BR UNT'),
        ('BPAC11', 'BTG Pactual UNT'),
        ('FLRY3', 'Fleury ON'),
        ('PRIO3', 'Prio ON'),
        ('RECV3', 'PetroReconcavo ON'),
        ('KLBN11', 'Klabin UNT'),
        ('CSAN3', 'Cosan ON'),
        ('RAIZ4', 'Raízen PN'),
        ('EQTL3', 'Equatorial ON'),
        ('SBSP3', 'Sabesp ON'),
    ]
    
    resultados = []
    for ticker, nome in acoes_brasileiras:
        if query in ticker or query in nome.upper():
            resultados.append({
                'ticker': ticker,
                'nome': nome,
                'tipo': 'stock'
            })
    
    return JsonResponse({'resultados': resultados[:15]})


@login_required
def buscar_cotacao_api(request):
    """Busca cotação via yfinance"""
    import yfinance as yf
    
    ticker = request.GET.get('ticker', '').strip().upper()
    
    if not ticker:
        return JsonResponse({'erro': 'Ticker não informado'}, status=400)
    
    try:
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
    """API para autocomplete - lista estática"""
    query = request.GET.get('q', '').strip().upper()
    
    if len(query) < 1:
        return JsonResponse({'resultados': []})
    
    # Principais ações brasileiras
    acoes = [
        ('PETR3', 'Petrobras ON'),
        ('PETR4', 'Petrobras PN'),
        ('VALE3', 'Vale ON'),
        ('ITUB3', 'Itaú Unibanco ON'),
        ('ITUB4', 'Itaú Unibanco PN'),
        ('BBDC3', 'Bradesco ON'),
        ('BBDC4', 'Bradesco PN'),
        ('BBAS3', 'Banco do Brasil ON'),
        ('ABEV3', 'Ambev ON'),
        ('B3SA3', 'B3 ON'),
        ('WEGE3', 'WEG ON'),
        ('RENT3', 'Localiza ON'),
        ('RAIL3', 'Rumo ON'),
        ('SUZB3', 'Suzano ON'),
        ('MGLU3', 'Magazine Luiza ON'),
        ('LREN3', 'Lojas Renner ON'),
        ('GGBR4', 'Gerdau PN'),
        ('USIM5', 'Usiminas PNA'),
        ('CSNA3', 'CSN ON'),
        ('ELET3', 'Eletrobras ON'),
        ('CMIG4', 'Cemig PN'),
        ('ENBR3', 'Energias BR ON'),
        ('SANB11', 'Santander BR UNT'),
        ('BPAC11', 'BTG Pactual UNT'),
        ('PRIO3', 'Prio ON'),
    ]
    
    resultados = []
    for ticker, nome in acoes:
        if query in ticker or query in nome.upper():
            resultados.append({
                'ticker': ticker,
                'nome': nome,
                'label': f"{ticker} - {nome}"
            })
    
    return JsonResponse({'resultados': resultados[:15]})


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
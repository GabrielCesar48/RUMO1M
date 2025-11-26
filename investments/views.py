from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Aporte
from .forms import AporteForm

@login_required
def adicionar_aporte(request):
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
    
    return render(request, 'investments/adicionar.html', {'form': form})

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
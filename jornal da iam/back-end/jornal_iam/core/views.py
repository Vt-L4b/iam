from django.shortcuts import render, get_object_or_404
from .models import Edicao, Destaques, Outros_grupos

def home(request):
    destaques = Destaques.objects.select_related('edicao').order_by('ordem')
    outros_grupos = Outros_grupos.objects.select_related('grupo').order_by('ordem')
    return render(request, 'core/home.html', {
        'destaques': destaques,
        'outros_grupos': outros_grupos,
    })


def edicoes(request):
    edicoes = Edicao.objects.select_related('grupo')
    return render(request, 'core/edicoes.html', {'edicoes': edicoes})


def edicao(request, pk):
    edicao = get_object_or_404(Edicao.objects.select_related('grupo'), pk=pk)
    return render(request, 'core/edicao.html', {'edicao': edicao})


def sobre(request):
    return render(request, 'core/sobre.html')

from django.shortcuts import render, get_object_or_404
from galeria.models import Fotografia

def index(request):
    fotografias = Fotografia.objects.order_by("-data_fotografia").filter(publicada=True)
    return render(request,'galeria/index.html', {"fotografias":fotografias})

def imagem360Animacao(request, foto_id):
    fotografia = get_object_or_404(Fotografia, pk=foto_id)
    return render(request, 'galeria/animacao.html', {"fotografia":fotografia})

def imagem360(request, foto_id):
    fotografia = get_object_or_404(Fotografia, pk=foto_id)
    return render(request, 'galeria/view360.html', {"fotografia":fotografia})
from django.shortcuts import render, get_object_or_404
from galeria.models import Fotografia, Categoria

def index(request):
    #fotografias = Fotografia.objects.order_by("categoria").filter(publicada=True)
    categorias = Categoria.objects.order_by("nome")
    return render(request,'galeria/index.html', {"categorias":categorias})

def imagem360Animacao(request, foto_id):
    fotografia = get_object_or_404(Fotografia, pk=foto_id)
    return render(request, 'galeria/animacao.html', {"fotografia":fotografia})

def imagem360(request, foto_id):
    fotografia = get_object_or_404(Fotografia, pk=foto_id)
    return render(request, 'galeria/view360.html', {"fotografia":fotografia})

def projeto(request, categoria_id):
    categoria = Categoria.objects.get(pk=categoria_id)
    fotografias = Fotografia.objects.order_by("nome").filter(categoria_id=categoria_id, publicada=True)
    return render(request,'galeria/projeto.html', {"fotografias":fotografias,"categoria": categoria})

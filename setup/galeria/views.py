from django.shortcuts import render, get_object_or_404
from galeria.models import Fotografia, Categoria, Album

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
    albuns = Album.objects.order_by("title").filter(categoria_id=categoria_id)
    return render(request,'galeria/projeto.html', {"fotografias":fotografias,"categoria": categoria, "albuns":albuns})

def album(request, album_id):
    album = get_object_or_404(Album, pk=album_id)
    fotografias = Fotografia.objects.order_by("nome").filter(album=album_id, publicada=True)
    return render(request,'galeria/album.html', {"fotografias":fotografias,"album": album})

def fotoAlbum360(request, nome, album_slug):
    album = get_object_or_404(Album, slug=album_slug)
    defaultYaw = album.defaultYaw
    defaultPitch = album.defaultPitch
    pan = album.sphereCorrection_pan
    tilt = album.sphereCorrection_tilt     
    roll = album.sphereCorrection_roll     
    fotografia = get_object_or_404(Fotografia,album__slug=album_slug, nome=nome)
    return render(request, 'galeria/fotoAlbum360.html', {"fotografia":fotografia, "defaultYaw":defaultYaw, "defaultPitch":defaultPitch, "pan":pan, "tilt":tilt, "roll": roll})




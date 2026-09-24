from django.shortcuts import render, get_object_or_404
from galeria.models import Fotografia, Categoria, Album
from django.db.models import IntegerField
from django.db.models.functions import Cast
from django.http import Http404


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
    fotografias = (
    Fotografia.objects
    .filter(album=album_id, publicada=True)
    .order_by(Cast("nome", IntegerField()))
    )
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

def streetView(request, album_id):
    album = get_object_or_404(Album, pk=album_id)
    defaultYaw = album.defaultYaw
    defaultPitch = album.defaultPitch
    pan = album.sphereCorrection_pan
    tilt = album.sphereCorrection_tilt     
    roll = album.sphereCorrection_roll  
    defaultYawInteger = int(defaultYaw.replace('deg', ''))
    fotos = Fotografia.objects.filter(album=album.id).order_by('id')
    inverterSentidoStreetView = album.inverterSentidoStreetView
    # ?foto=12 vem do mapa. Os nodes começam em 1, o índice do KML começa em 0.
    try:
        indice = int(request.GET.get("foto", 0))
    except ValueError:
        indice = 0
    total = fotos.count()
    start_node = max(1, min(indice + 1, total)) if total else 1

    return render(request, 'galeria/streetview.html', {
        "album": album, "fotos": fotos, "defaultYaw": defaultYaw,
        "defaultYawInteger": defaultYawInteger, "defaultPitch": defaultPitch,
        "pan": pan, "tilt": tilt, "roll": roll,
        "inverterSentidoStreetView": inverterSentidoStreetView,
        "start_node": start_node,
        "kml_url": album.arquivo_kml.url if album.arquivo_kml else "",
    })

def mapa(request, pk):
    album = get_object_or_404(Album, pk=pk)
    if not album.arquivo_kml:
        raise Http404("Este álbum não tem arquivo KML.")
    return render(request, "galeria/mapa.html", {
        "album": album,
        "kml_url": album.arquivo_kml.url,
    })
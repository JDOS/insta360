from django.urls import path
from galeria.views import index, imagem360Animacao, imagem360, projeto, album, fotoAlbum360, streetView

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', index, name='index'),
    path('imagem/360/animacao/<int:foto_id>', imagem360Animacao, name='imagem360Animacao'),
    path('imagem/360/<int:foto_id>', imagem360, name='imagem360'),
    path('projeto/360/<int:categoria_id>', projeto, name='projeto'),
    path('projeto/360/album/<int:album_id>', album, name='album'),
    path('projeto/360/album/<slug:album_slug>/foto/<str:nome>', fotoAlbum360, name='fotoAlbum360'),
    path('projeto/360/streetview/<int:album_id>', streetView, name='streetView'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
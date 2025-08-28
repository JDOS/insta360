from django.urls import path
from galeria.views import index, imagem360Animacao, imagem360

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', index, name='index'),
    path('imagem/360/animacao/<int:foto_id>', imagem360Animacao, name='imagem360Animacao'),
    path('imagem/360/<int:foto_id>', imagem360, name='imagem360'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
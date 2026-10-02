from django.db.models import IntegerField
from django.db.models.functions import Cast

from .models import Fotografia


def reordenar_nomes(album_id):
    """Renumera as fotos do álbum em sequência (0, 1, 2, ...) mantendo a ordem atual."""
    fotos = list(
        Fotografia.objects
        .filter(album_id=album_id)
        .annotate(nome_int=Cast('nome', IntegerField()))
        .order_by('nome_int', 'id')
    )

    alteradas = []
    for index, foto in enumerate(fotos):
        novo_nome = str(index)
        if foto.nome != novo_nome:
            foto.nome = novo_nome
            alteradas.append(foto)

    if alteradas:
        Fotografia.objects.bulk_update(alteradas, ['nome'])
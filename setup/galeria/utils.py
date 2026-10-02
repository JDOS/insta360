from django.db.models import IntegerField
from django.db.models.functions import Cast

from .models import Fotografia
from PIL import Image

import io
import os
from django.core.files.base import ContentFile

GPS_IFD = 0x8825

Image.MAX_IMAGE_PIXELS = None  # panoramas grandes passam do limite padrão

LARGURA_MAX = 8000
QUALIDADE = 85

def fotos_em_ordem(album):
    """Ordem oficial das fotos do álbum: a mesma do nome (0, 1, 2...)."""
    return album.photos.order_by(Cast("nome", IntegerField()), "id")

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



def _para_decimal(dms, ref):
    graus, minutos, segundos = (float(x) for x in dms)
    valor = graus + minutos / 60 + segundos / 3600
    return -valor if ref in ("S", "W") else valor


def extrair_gps(arquivo):
    """Retorna (latitude, longitude) do EXIF da imagem, ou (None, None) se não houver GPS."""
    try:
        arquivo.seek(0)
        with Image.open(arquivo) as img:
            gps = img.getexif().get_ifd(GPS_IFD)
    except Exception:
        return None, None
    finally:
        try:
            arquivo.seek(0)  # devolve o ponteiro para o Django conseguir salvar o arquivo
        except Exception:
            pass

    if not gps or 2 not in gps or 4 not in gps:
        return None, None

    latitude = _para_decimal(gps[2], gps.get(1, "N"))
    longitude = _para_decimal(gps[4], gps.get(3, "E"))
    return latitude, longitude


def reduzir_imagem(arquivo, largura=LARGURA_MAX, qualidade=QUALIDADE):
    """Reduz a imagem para no máximo `largura` px, mantendo a proporção e o EXIF."""
    arquivo.seek(0)
    with Image.open(arquivo) as original:
        exif = original.info.get("exif")  # contém o GPS
        xmp = original.info.get("xmp")    # metadados de panorama 360, quando existem

        img = original.convert("RGB") if original.mode != "RGB" else original
        if img.width > largura:
            altura = round(img.height * largura / img.width)
            img = img.resize((largura, altura), Image.LANCZOS)

        params = {"quality": qualidade, "optimize": True, "progressive": True}
        if exif:
            params["exif"] = exif
        if xmp:
            params["xmp"] = xmp

        buffer = io.BytesIO()
        img.save(buffer, "JPEG", **params)

    nome = os.path.splitext(os.path.basename(arquivo.name))[0] + ".jpg"
    return ContentFile(buffer.getvalue(), name=nome)
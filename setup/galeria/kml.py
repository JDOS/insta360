import os
from xml.sax.saxutils import escape

from django.conf import settings
from django.core.files.base import ContentFile
from django.db.models import IntegerField
from django.db.models.functions import Cast
from django.urls import reverse
from .utils import fotos_em_ordem


def _fotos_com_coordenadas(album):
    return list(
        album.photos
        .filter(latitude__isnull=False, longitude__isnull=False)
        .order_by(Cast("nome", IntegerField()), "id")
    )


def _link_streetview(album, posicao, request=None):
    caminho = reverse("streetView", kwargs={"album_id": album.pk}) + f"?foto={posicao}"
    site_url = getattr(settings, "SITE_URL", "").rstrip("/")
    if site_url:
        return site_url + caminho
    if request:
        return request.build_absolute_uri(caminho)
    return caminho


def _link_foto(album, foto, request=None):
    caminho = reverse("streetView", kwargs={"album_slug": album.id, "nome": foto.nome})
    site_url = getattr(settings, "SITE_URL", "").rstrip("/")
    if site_url:
        return site_url + caminho
    if request:
        return request.build_absolute_uri(caminho)
    return caminho


def _coord(foto):
    # KML usa a ordem longitude,latitude,altitude
    return f"{foto.longitude:.7f},{foto.latitude:.7f},0"


def gerar_kml(album, request=None):
    """Monta o conteúdo do KML. Retorna (texto_kml, quantidade_de_pontos)."""
    todas = list(fotos_em_ordem(album))

    # Posição de cada foto na lista do street view (inclui as fotos sem coordenadas)
    fotos = [
        (posicao, foto)
        for posicao, foto in enumerate(todas)
        if foto.latitude is not None and foto.longitude is not None
    ]
    if not fotos:
        return None, 0


    marcadores = []
    for posicao, foto in fotos:
        url = _link_streetview(album, posicao, request)
        arquivo = os.path.splitext(os.path.basename(foto.foto.name))[0] if foto.foto else ""
        marcadores.append(f"""    <Placemark>
      <name>{escape(foto.nome)}</name>
      <description><![CDATA[{escape(arquivo)}<br/>Latitude: {foto.latitude:.6f}, Longitude: {foto.longitude:.6f}<br/><a href="{url}" target="_blank">Ver foto 360 ({escape(foto.nome)})</a>]]></description>
      <styleUrl>#pontoFoto</styleUrl>
      <Point>
        <coordinates>{_coord(foto)}</coordinates>
      </Point>
    </Placemark>""")

    kml = f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>{escape(album.title)}</name>
    <Style id="pontoFoto">
      <IconStyle>
        <scale>1.0</scale>
      </IconStyle>
    </Style>
{chr(10).join(marcadores)}
  </Document>
</kml>
"""
    return kml, len(fotos)


def salvar_kml(album, request=None):
    """Gera o KML e grava no campo arquivo_kml do álbum. Retorna a quantidade de pontos."""
    kml, total = gerar_kml(album, request)
    if not kml:
        return 0

    # Remove o arquivo anterior para o novo manter o nome limpo (slug.kml)
    if album.arquivo_kml:
        album.arquivo_kml.delete(save=False)

    album.arquivo_kml.save(f"{album.slug}.kml", ContentFile(kml.encode("utf-8")), save=True)
    return total
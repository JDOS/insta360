import os

from django.core.management.base import BaseCommand, CommandError
from PIL import Image

from galeria.models import Album, Fotografia
from galeria.utils import extrair_gps, reduzir_imagem


class Command(BaseCommand):
    help = "Reduz o tamanho dos panoramas de um álbum, preservando o EXIF (GPS)."

    def add_arguments(self, parser):
        parser.add_argument("album_id", type=int, help="ID do álbum")
        parser.add_argument("--largura", type=int, default=8000)
        parser.add_argument("--qualidade", type=int, default=82)
        parser.add_argument("--dry-run", action="store_true",
                            help="Apenas mostra o que seria feito")

    def handle(self, *args, **opts):
        try:
            album = Album.objects.get(pk=opts["album_id"])
        except Album.DoesNotExist:
            raise CommandError(f"Álbum {opts['album_id']} não existe.")

        fotos = Fotografia.objects.filter(album=album).order_by("id")
        self.stdout.write(f"Álbum: {album.title} — {fotos.count()} fotos")

        largura = opts["largura"]
        qualidade = opts["qualidade"]
        dry_run = opts["dry_run"]

        total_antes = total_depois = 0
        reduzidas = puladas = 0

        for f in fotos:
            if not f.foto:
                continue

            caminho = f.foto.path
            if not os.path.exists(caminho):
                self.stdout.write(self.style.WARNING(f"  faltando {f.id}: {caminho}"))
                continue

            antes = os.path.getsize(caminho)
            total_antes += antes

            with Image.open(caminho) as img:
                largura_atual = img.width

            # Já está no tamanho certo: não recomprime (cada recompressão perde qualidade)
            if largura_atual <= largura:
                total_depois += antes
                puladas += 1
                self.stdout.write(f"  pulada {f.id}: já tem {largura_atual}px")
                continue

            if dry_run:
                reduzidas += 1
                self.stdout.write(
                    f"  [dry] {f.id}: {largura_atual}px, {antes/1e6:.1f} MB → seria reduzida"
                )
                continue

            with open(caminho, "rb") as arq:
                # Aproveita para preencher o GPS de fotos antigas que ainda não têm
                if f.latitude is None:
                    lat, lon = extrair_gps(arq)
                    if lat is not None:
                        Fotografia.objects.filter(pk=f.pk).update(latitude=lat, longitude=lon)

                reduzida = reduzir_imagem(arq, largura, qualidade)

            # Grava num arquivo temporário e só depois substitui o original
            temporario = caminho + ".tmp"
            with open(temporario, "wb") as arq:
                arq.write(reduzida.read())
            os.replace(temporario, caminho)

            depois = os.path.getsize(caminho)
            total_depois += depois
            reduzidas += 1
            self.stdout.write(f"  ok {f.id}: {antes/1e6:.1f} MB → {depois/1e6:.1f} MB")

        if dry_run:
            self.stdout.write(self.style.SUCCESS(
                f"{reduzidas} foto(s) seriam reduzidas, {puladas} já estão no tamanho."
            ))
        elif total_antes:
            self.stdout.write(self.style.SUCCESS(
                f"{reduzidas} reduzida(s), {puladas} pulada(s). "
                f"Total: {total_antes/1e6:.0f} MB → {total_depois/1e6:.0f} MB"
            ))
import os
from django.core.management.base import BaseCommand, CommandError
from PIL import Image
from galeria.models import Album, Fotografia

Image.MAX_IMAGE_PIXELS = None  # panoramas grandes passam do limite padrão


class Command(BaseCommand):
    help = "Reduz o tamanho dos panoramas de um álbum."

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
        total_antes = total_depois = 0

        for f in fotos:
            if not f.foto:
                continue
            caminho = f.foto.path
            antes = os.path.getsize(caminho)
            total_antes += antes

            if opts["dry_run"]:
                self.stdout.write(f"  [dry] {os.path.basename(caminho)} — {antes/1e6:.1f} MB")
                continue

            img = Image.open(caminho)
            if img.mode != "RGB":
                img = img.convert("RGB")
            if img.width > largura:
                img = img.resize((largura, largura // 2), Image.LANCZOS)

            img.save(caminho, "JPEG", quality=opts["qualidade"],
                     optimize=True, progressive=True)

            depois = os.path.getsize(caminho)
            total_depois += depois
            self.stdout.write(
                f"  ok {f.id}: {antes/1e6:.1f} MB → {depois/1e6:.1f} MB"
            )

        if not opts["dry_run"] and total_antes:
            self.stdout.write(self.style.SUCCESS(
                f"Total: {total_antes/1e6:.0f} MB → {total_depois/1e6:.0f} MB"
            ))
import os

from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db.models import FileField


class Command(BaseCommand):
    help = "Lista e apaga arquivos da pasta de mídia que nenhum registro usa."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true",
                            help="Apenas lista os arquivos órfãos, sem apagar")
        parser.add_argument("--sim", action="store_true",
                            help="Apaga sem pedir confirmação")
        parser.add_argument("--ignorar", nargs="*", default=[],
                            help="Pastas dentro da mídia que não devem ser tocadas. Ex: --ignorar backup logos")

    def handle(self, *args, **opts):
        raiz = settings.MEDIA_ROOT
        if not raiz or not os.path.isdir(raiz):
            raise CommandError(f"MEDIA_ROOT inválido: {raiz!r}")

        # 1. Todos os arquivos referenciados por qualquer FileField/ImageField do projeto
        em_uso = set()
        for model in apps.get_models():
            campos = [f.name for f in model._meta.get_fields() if isinstance(f, FileField)]
            for campo in campos:
                nomes = model._default_manager.values_list(campo, flat=True).iterator()
                em_uso.update(n.replace("\\", "/") for n in nomes if n)

        self.stdout.write(f"Arquivos referenciados no banco: {len(em_uso)}")

        # 2. Arquivos no disco que não estão nessa lista
        ignorar = [p.strip("/\\").replace("\\", "/") + "/" for p in opts["ignorar"]]
        orfaos, total = [], 0

        for pasta, _, arquivos in os.walk(raiz):
            for arq in arquivos:
                caminho = os.path.join(pasta, arq)
                rel = os.path.relpath(caminho, raiz).replace(os.sep, "/")
                if rel in em_uso or any(rel.startswith(i) for i in ignorar):
                    continue
                orfaos.append((rel, caminho))
                total += os.path.getsize(caminho)

        if not orfaos:
            self.stdout.write(self.style.SUCCESS("Nenhum arquivo órfão encontrado."))
            return

        for rel, caminho in sorted(orfaos):
            self.stdout.write(f"  {rel}  ({os.path.getsize(caminho) / 1e6:.1f} MB)")
        self.stdout.write(f"\n{len(orfaos)} arquivo(s) órfão(s), {total / 1e6:.1f} MB no total.")

        if opts["dry_run"]:
            self.stdout.write(self.style.WARNING("Dry-run: nada foi apagado."))
            return

        if not opts["sim"]:
            resposta = input("Apagar esses arquivos? [s/N] ").strip().lower()
            if resposta != "s":
                self.stdout.write("Cancelado.")
                return

        # 3. Apaga os órfãos
        for rel, caminho in orfaos:
            try:
                os.remove(caminho)
            except OSError as e:
                self.stdout.write(self.style.WARNING(f"  não apagou {rel}: {e}"))

        # 4. Remove pastas que ficaram vazias (ex: fotos/2026/09/08/)
        for pasta, _, _ in os.walk(raiz, topdown=False):
            if pasta != raiz and not os.listdir(pasta):
                os.rmdir(pasta)

        self.stdout.write(self.style.SUCCESS(f"{len(orfaos)} arquivo(s) apagado(s), {total / 1e6:.1f} MB liberados."))
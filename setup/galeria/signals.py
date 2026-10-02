from django.db import transaction
from django.db.models.signals import post_delete, pre_save

from .models import Album, Categoria, Fotografia

from .utils import reordenar_nomes

CAMPOS = {
    Fotografia: ["foto"],
    Album: ["foto", "arquivo_kml"],
    Categoria: ["foto"],
}


def arquivo_em_uso(nome):
    """Evita apagar um arquivo que outro registro ainda usa."""
    return any(
        model.objects.filter(**{campo: nome}).exists()
        for model, campos in CAMPOS.items()
        for campo in campos
    )


def apagar_arquivo(arquivo):
    if not arquivo:
        return
    nome, storage = arquivo.name, arquivo.storage

    def _apagar():
        if not arquivo_em_uso(nome) and storage.exists(nome):
            storage.delete(nome)

    # Só apaga depois que o banco confirmou a operação
    transaction.on_commit(_apagar)


def ao_deletar(sender, instance, **kwargs):
    for campo in CAMPOS[sender]:
        apagar_arquivo(getattr(instance, campo))


def ao_salvar(sender, instance, **kwargs):
    if not instance.pk:
        return
    antigo = sender.objects.filter(pk=instance.pk).first()
    if not antigo:
        return
    for campo in CAMPOS[sender]:
        velho, novo = getattr(antigo, campo), getattr(instance, campo)
        if velho and velho.name != novo.name:
            apagar_arquivo(velho)


for model in CAMPOS:
    post_delete.connect(ao_deletar, sender=model)
    pre_save.connect(ao_salvar, sender=model)

def reordenar_ao_deletar_foto(sender, instance, **kwargs):
    album_id = instance.album_id

    def _reordenar():
        # Se o álbum inteiro foi excluído (cascade), não há o que reordenar
        if Album.objects.filter(pk=album_id).exists():
            reordenar_nomes(album_id)

    transaction.on_commit(_reordenar)


post_delete.connect(reordenar_ao_deletar_foto, sender=Fotografia)
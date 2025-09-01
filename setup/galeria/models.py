from django.db import models
from datetime import datetime

class Categoria(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True)
    descricao = models.TextField(blank=True)
    foto = models.ImageField(upload_to="fotos/%Y/%m/%d/", blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["nome"]
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"

    def __str__(self):
        return self.nome


class Fotografia(models.Model):

    nome = models.CharField(max_length=100, null=False, blank=False)
    legenda = models.CharField(max_length=150, null=True, blank=True)
    descricao = models.TextField(null=True, blank=True)
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,     
        related_name="fotografias",
        null=True, blank=True
    )
    foto = models.ImageField(upload_to="fotos/%Y/%m/%d/", blank=True)
    publicada = models.BooleanField(default=False)
    data_fotografia = models.DateTimeField(default=datetime.now, blank=False)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["categoria__nome", "nome"]
        verbose_name = "Fotografia"
        verbose_name_plural = "Fotografias"

    def __str__(self):
        return self.nome
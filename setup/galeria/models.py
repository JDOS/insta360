from django.db import models
from datetime import datetime
from django.utils.text import slugify

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
    
class Album(models.Model):
    title = models.CharField('Título', max_length=200)
    foto = models.ImageField(upload_to="fotos/%Y/%m/%d/", blank=True)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,     
        related_name="album_categoria",
        null=True, blank=True
    )
    created_at = models.DateTimeField('Criado em', auto_now_add=True)

    def save(self, *args, **kwargs):
            if not self.slug:
                self.slug = slugify(self.nome) or f"foto-{self.id}"
            super().save(*args, **kwargs)
            
    class Meta:
        verbose_name = 'Álbum'
        verbose_name_plural = 'Álbuns'

    def __str__(self):
        return self.title




class Fotografia(models.Model):
    album = models.ForeignKey(Album, related_name='photos', on_delete=models.CASCADE, null=True, blank=True, verbose_name='Álbum')
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
    publicada = models.BooleanField(default=True)
    data_fotografia = models.DateTimeField(default=datetime.now, blank=False)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["categoria__nome", "nome"]
        verbose_name = "Fotografia"
        verbose_name_plural = "Fotografias"

    def __str__(self):
        return self.nome
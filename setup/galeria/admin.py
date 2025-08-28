from django.contrib import admin

from .models import Fotografia, Categoria

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nome", "slug")
    search_fields = ("nome",)
    prepopulated_fields = {"slug": ("nome",)}  # preenche o slug automaticamente a partir do nome
    ordering = ("nome",)

@admin.register(Fotografia)
class FotografiaAdmin(admin.ModelAdmin):
    list_display = ("nome", "categoria", "criado_em")
    list_filter = ("categoria",)
    search_fields = ("nome",)
    autocomplete_fields = ("categoria",)
    ordering = ("categoria__nome", "nome")


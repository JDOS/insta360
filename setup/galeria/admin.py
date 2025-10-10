from django.contrib import admin, messages
from django.shortcuts import redirect, render, get_object_or_404

from .models import Fotografia, Categoria, Album
from django.urls import path, reverse

from django.utils.html import format_html

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nome", "slug")
    search_fields = ("nome",)
    prepopulated_fields = {"slug": ("nome",)}  # preenche o slug automaticamente a partir do nome
    ordering = ("nome",)

@admin.register(Fotografia)
class FotografiaAdmin(admin.ModelAdmin):
    list_display = ("nome", "categoria", "criado_em", "album")
    list_filter = ("categoria",)
    search_fields = ("nome",)
    autocomplete_fields = ("categoria",)
    ordering = ("categoria__nome", "nome")


class PhotoInline(admin.TabularInline):
    model = Fotografia
    extra = 0
    readonly_fields = ('image_preview',)
    fields = ('foto',)
    
    def image_preview(self, obj):
        if obj.foto:
            return format_html('<img src="{}" style="max-height: 50px;" />', obj.foto.url)
        return '-'
    image_preview.short_description = 'Preview'


@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'photo_count','slug', 'created_at')
    list_display_links = ('title',)
    search_fields = ('title',)
    inlines = [PhotoInline]
    
    def photo_count(self, obj):
        return obj.photos.count()
    photo_count.short_description = 'Nº Fotos'
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:object_id>/bulk-upload/',
                self.admin_site.admin_view(self.bulk_upload_view),
                name='galeria_album_bulk_upload',
            ),
        ]
        return custom_urls + urls
    
    def bulk_upload_view(self, request, object_id):
        album = get_object_or_404(Album, pk=object_id)
        
        if request.method == 'POST':
            # Pegar TODOS os arquivos
            images = request.FILES.getlist('images')
            
            if not images:
                messages.error(request, '❌ Nenhuma imagem foi enviada!')
                return render(request, 'admin/galeria/album/bulk_upload.html', {
                    **self.admin_site.each_context(request),
                    'opts': self.model._meta,
                    'original': album,
                    'title': f'Upload múltiplo - {album.title}',
                    'album': album,
                })

            ultima_foto = Fotografia.objects.filter(album=object_id).order_by('-id').first()
            if ultima_foto:
                ultimo_nome = int(ultima_foto.nome) + 1
            else:
                ultimo_nome=0

            # ORDENAR por nome (ordem crescente)
            images_sorted = sorted(images, key=lambda x: x.name)
            # Criar fotos sem validação complexa (para testar)
            photos = [Fotografia(album=album, foto=img, nome=str(ultimo_nome+index)) for index,img in enumerate(images_sorted)]
            
            Fotografia.objects.bulk_create(photos)
            
            messages.success(request, f'✅ {len(images)} foto(s) adicionada(s) com sucesso!')
            return redirect('admin:galeria_album_change', object_id=album.pk)
        
        context = {
            **self.admin_site.each_context(request),
            'opts': self.model._meta,
            'original': album,
            'title': f'Upload múltiplo - {album.title}',
            'album': album,
        }
        return render(request, 'admin/galeria/album/bulk_upload.html', context)
    
    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_bulk_upload'] = True
        return super().change_view(request, object_id, form_url, extra_context)


# @admin.register(Fotografia)
# class PhotoAdmin(admin.ModelAdmin):
#     list_display = ('id', 'image_preview', 'album', 'uploaded_at')
#     list_filter = ('album', 'uploaded_at')
#     readonly_fields = ('image_preview', 'uploaded_at')
    
#     def image_preview(self, obj):
#         if obj.image:
#             return format_html('<img src="{}" style="max-height: 100px;" />', obj.image.url)
#         return '-'
#     image_preview.short_description = 'Preview'
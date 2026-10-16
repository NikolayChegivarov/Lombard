from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from .models import CarouselImage


@admin.register(CarouselImage)
class CarouselImageAdmin(admin.ModelAdmin):
    list_display = ('preview', 'title', 'order', 'is_active', 'created_at')
    list_display_links = ('preview', 'title')
    list_editable = ('order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('title',)
    ordering = ('order', 'id')
    readonly_fields = ('created_at', 'preview_large')

    fieldsets = (
        (None, {
            'fields': ('image', 'preview_large', 'title')
        }),
        ('Отображение', {
            'fields': ('order', 'is_active')
        }),
        ('Служебное', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='Превью')
    def preview(self, obj):
        if not obj.image:
            return '—'
        return format_html(
            '<img src="{}" style="height:42px;border-radius:6px;object-fit:cover;" />',
            obj.image.url,
        )

    @admin.display(description='Большое превью')
    def preview_large(self, obj):
        if not obj or not obj.image:
            return 'Изображение появится после загрузки'
        return mark_safe(
            f'<img src="{obj.image.url}" '
            f'style="max-width:640px;width:100%;border-radius:10px;" />'
        )
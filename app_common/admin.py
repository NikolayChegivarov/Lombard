from django.contrib import admin

from .models import News


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'published_at', 'is_published', 'created_at')
    list_filter = ('is_published', 'published_at')
    search_fields = ('title', 'text')
    date_hierarchy = 'published_at'
    ordering = ('-published_at',)

    fieldsets = (
        ('Основное', {
            'fields': ('title', 'text')
        }),
        ('Публикация', {
            'fields': ('published_at', 'is_published'),
            'description': 'Снимите галочку «Опубликовано», чтобы скрыть новость с сайта'
        }),
    )
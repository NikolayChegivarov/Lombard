from .models import News


def news_context(request):
    """Добавляет в контекст всех шаблонов флаг наличия новостей."""
    return {
        'has_news': News.objects.filter(is_published=True).exists(),
    }
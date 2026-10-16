from django import template

from app_carousel.models import CarouselImage

register = template.Library()


@register.simple_tag
def get_carousel_images():
    """Возвращает список активных изображений карусели в заданном порядке."""
    return list(
        CarouselImage.objects
        .filter(is_active=True)
        .order_by('order', 'id')
    )
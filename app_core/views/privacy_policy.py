"""
View страницы политики обработки персональных данных.
"""
from django.views.generic import TemplateView


class PrivacyPolicyView(TemplateView):
    """Статическая страница политики обработки ПД."""
    template_name = 'core/privacy_policy.html'
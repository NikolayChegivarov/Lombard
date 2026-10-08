from django.urls import path

from .views import user_calculators

app_name = 'app_prices'

urlpatterns = [
    path('api/metal-prices/', user_calculators.metal_prices_api, name='metal_prices_api'),
]
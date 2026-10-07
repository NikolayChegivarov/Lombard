from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # 👇 API-маршруты приложения app_branches
    path('', include('app_branches.urls', namespace='app_branches')),

    # 👇 Временно закомментированы (views ещё не готовы)
    # path('', include('app_prices.urls', namespace='app_prices')),
    # path('', include('app_common.urls', namespace='app_common')),
    # path('', include('app_accounts.urls', namespace='app_accounts')),

    # 👇 Главная и другие страницы app_core
    path('', include('app_core.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
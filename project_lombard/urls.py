from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    path('branches/', include('app_branches.urls', namespace='app_branches')),

    # 👇 Временно можно закомментировать, пока не готовы views
    # path('prices/', include('app_prices.urls', namespace='app_prices')),
    # path('', include('app_common.urls', namespace='app_common')),
    # path('', include('app_accounts.urls', namespace='app_accounts')),

    path('', include('app_core.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
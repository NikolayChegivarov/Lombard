"""
URL-маршруты приложения accounts.

Назначение:
  - Вход (телефон → SMS-код), выход.
  - Личный кабинет (открытые билеты).
  - Закрытые билеты с пагинацией.

Все маршруты имеют префикс /account/ (подключается в project_lombard/urls.py).
"""
from django.urls import path

from . import views

app_name = 'app_accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('verify/', views.verify_code_view, name='verify_code'),
    path('', views.dashboard_view, name='dashboard'),
    path('closed/', views.closed_tickets_view, name='closed_tickets'),
    path('logout/', views.logout_view, name='logout'),
]
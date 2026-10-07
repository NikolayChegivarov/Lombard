from django.urls import path

from app_branches import views

app_name = 'app_branches'

urlpatterns = [
    path('api/set-city/', views.set_city_view, name='set_city'),
    path('api/branches/', views.branches_api_view, name='branches_api'),
]
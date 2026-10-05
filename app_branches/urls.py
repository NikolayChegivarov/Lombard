from django.urls import path
from .views import branches_view

app_name = 'app_branches'

urlpatterns = [
    path('', branches_view, name='branches'),
]

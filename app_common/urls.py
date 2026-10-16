from django.urls import path
from . import views

app_name = 'app_common'

urlpatterns = [
    path('conditions/', views.conditions_view, name='conditions'),
    path('news/', views.news_view, name='news'),
    path('questions-answers/', views.questions_view, name='questions'),
    path('contacts/', views.contacts_view, name='contacts'),
    path('about-us/', views.about_us_view, name='about_us'),
]
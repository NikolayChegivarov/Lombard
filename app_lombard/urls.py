from django.urls import path
from .views.base import index, prices_view, questions_answers_view, news_view, contacts_view, about_us
from .views import branches, conditions

urlpatterns = [
    path('', index, name='index'),
    path('branches/', branches.branches_view, name='branches'),
    path('conditions/', conditions.conditions_view, name='conditions'),
    path('prices/', prices_view, name='prices'),
    path('questions-answers/', questions_answers_view, name='questions_answers'),
    path('news/', news_view, name='news'),
    path('contacts/', contacts_view, name='contacts'),
    path('about/', about_us, name='about_us'),
]
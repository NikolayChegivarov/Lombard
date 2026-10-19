from django.shortcuts import render

from app_branches.models import Branch

from .models import News


def conditions_view(request):
    return render(request, 'conditions.html')


def news_view(request):
    news_list = News.objects.filter(is_published=True)
    return render(request, 'news.html', {'news_list': news_list})


def questions_view(request):
    return render(request, 'questions_answers.html')


def contacts_view(request):
    return render(request, 'contacts.html')


def about_us_view(request):
    return render(request, 'about_us.html')
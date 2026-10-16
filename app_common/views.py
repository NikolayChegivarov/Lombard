from django.shortcuts import render


def conditions_view(request):
    return render(request, 'conditions.html')


def news_view(request):
    return render(request, 'news.html')


def questions_view(request):
    return render(request, 'questions_answers.html')


def contacts_view(request):
    return render(request, 'contacts.html')


def about_us_view(request):
    return render(request, 'about_us.html')
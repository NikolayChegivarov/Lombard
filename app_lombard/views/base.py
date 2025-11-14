from django.shortcuts import render

def index(request):
    return render(request, 'index.html')

def prices_view(request):
    return render(request, 'prices.html')

def questions_answers_view(request):
    return render(request, 'questions_answers.html')

def news_view(request):
    return render(request, 'news.html')

def contacts_view(request):
    return render(request, 'contacts.html')
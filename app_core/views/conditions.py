from django.shortcuts import render

def conditions_view(request):
    return render(request, 'conditions.html')
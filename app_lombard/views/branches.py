from django.shortcuts import render

def branches_view(request):
    return render(request, 'branches.html')
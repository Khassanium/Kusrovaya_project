from django.shortcuts import render

def home(request):
    return render(request, 'map_app/index.html')  # <- Добавь 'map_app/'
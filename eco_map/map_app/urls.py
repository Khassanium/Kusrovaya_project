from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('ml-analysis/', views.ml_analysis, name='ml-analysis'),
]
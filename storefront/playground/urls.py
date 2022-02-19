from django.urls import path
from . import views

# URL Configuration Module
urlpatterns = [
    path('hello/', views.say_hello) # Returns URLPattern object
]
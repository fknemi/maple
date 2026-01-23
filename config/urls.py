# config/urls.py
from django.contrib import admin
from django.urls import path, include
from core import views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    path('', views.home, name='home'),
    path('register/', views.register_page, name='register_page'),
    path('login/', views.login_page, name='login_page'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('tasks/', views.tasks, name='tasks'),
    path('habits/', views.habits, name='habits'),
    path('stats/', views.stats, name='stats'),
    path('profile/', views.profile, name='profile'),
    path('account/', views.account, name='account'),
    
    path('api/', include('core.urls')),
]

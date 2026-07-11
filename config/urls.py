"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from tracker import views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Tracker core views
    path('', views.dashboard, name='dashboard'),
    path('balance-summary/', views.balance_summary, name='balance_summary'),
    path('toggle-meal/', views.toggle_meal, name='toggle_meal'),
    path('add-transaction/', views.add_transaction, name='add_transaction'),
    path('settings/', views.settings_view, name='settings'),
    path('history/', views.history_view, name='history'),

    # Authentication views
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
]

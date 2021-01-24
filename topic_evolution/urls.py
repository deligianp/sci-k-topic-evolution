"""topic_evolution URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
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
from django.contrib.auth import views as auth_views
from django.urls import path, include
from rest_framework import routers
from topic_evolution_visualization import views
from topic_evolution_visualization.api import urls

from topic_evolution_visualization import urls as topic_evolution_visualization_urls

router = routers.DefaultRouter()
urlpatterns = [
    path('', include(topic_evolution_visualization_urls)),
    # path("accounts/", include("django.contrib.auth.urls")),
    path('accounts/login/', auth_views.LoginView.as_view()),
    path('admin/', admin.site.urls),
    path('api/', include(urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]

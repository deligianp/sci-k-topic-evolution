from django.urls import path

from .views import model_topics, models, analyze_text

urlpatterns = [
    path('model-topics', model_topics),
    path('models', models),
    path('analyze-text', analyze_text)
]

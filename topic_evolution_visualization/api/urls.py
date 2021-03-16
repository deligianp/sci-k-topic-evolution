from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import model_topics, models, analyze_text, topic_evolution, model_novel_topics

router = DefaultRouter()
urlpatterns = [
    path('', include(router.urls)),
    path('model-topics', model_topics),
    path('models', models),
    path('analyze-text', analyze_text),
    path('topic-evolution', topic_evolution),
    path('novel-topics', model_novel_topics)
]

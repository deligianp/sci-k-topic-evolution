from rest_framework.decorators import api_view
from rest_framework.response import Response

from resources import lda_query
from topic_evolution_visualization import queries


@api_view()
def model_topics(request):
    target_model_name = request.GET.get("name", None)
    offset = request.GET.get("offset", 0)
    limit = request.GET.get("limit", 50)
    topic = request.GET.get("topic", None)
    data = dict()
    main_model = queries.get_model(name=target_model_name)
    if main_model:
        topics = queries.get_topics_terms_representation(
            main_model,
            *(topic,) if topic else tuple(range(offset, offset + limit))
        )
        if topic:
            data = {
                "name": main_model.name,
                "description": main_model.description,
                "training_context": main_model.training_context,
                "topics": topics
            }
    return Response(data)


@api_view()
def models(request):
    return Response(queries.get_models())


@api_view(http_method_names=["POST"])
def analyze_text(request):
    text = request.data.get("text")
    model_name = request.data.get("model_name", None)
    result = lda_query.analyze_text(text, model_name)
    return Response(result)

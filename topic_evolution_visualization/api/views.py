from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from resources import lda_query
from topic_evolution_visualization import queries


@api_view()
def model_topics(request):
    # Parse required parameter "name"
    target_model_name = request.GET.get("name", None)
    if not target_model_name:
        return Response(
            data={
                "message": "Request must provide the name of the model, to which the target topics relate to"
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    model = queries.get_model(name=target_model_name)
    if not model:
        return Response(
            data={
                "message": "Requested model \"{}\" does not exist".format(target_model_name)
            },
            status=status.HTTP_404_NOT_FOUND
        )
    n_topics = queries.get_number_of_topics(model)

    topic = None
    offset = 0
    limit = None
    n_terms = None

    # Parse topic
    target_topic = request.GET.get("topic", None)
    target_offset = request.GET.get('offset', None)
    target_limit = request.GET.get('limit', None)
    if target_topic:
        try:
            topic = int(target_topic)
            if topic < 0:
                return Response(
                    data={
                        "message": "Requested topic index must be a positive integer or 0"
                    },
                    status=status.HTTP_422_UNPROCESSABLE_ENTITY
                )
            elif topic >= n_topics:
                return Response(
                    data={
                        'message': 'Requested topic does not exist in model "{}"'.format(target_model_name)
                    },
                    status=status.HTTP_404_NOT_FOUND
                )
            offset = topic
            limit = 1
        except ValueError:
            topic = target_topic
    else:
        # Parse offset
        try:
            offset = int(target_offset) if target_offset else 0
        except ValueError:
            return Response(
                data={
                    "message": "Offset must be a positive integer or 0"
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        if offset < 0:
            return Response(
                data={
                    "message": "Offset must be a positive integer or 0"
                },
                status=status.HTTP_422_UNPROCESSABLE_ENTITY
            )
        elif offset >= n_topics:
            return Response(
                data={
                    'message': 'Offset exceeds the total number of topics of model "{}"'.format(target_model_name)
                },
                status=status.HTTP_404_NOT_FOUND
            )

        # Parse limit
        try:
            limit = int(target_limit) if target_limit else n_topics - offset
        except ValueError:
            return Response(
                data={
                    "message": "Limit must be a positive integer"
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        if limit < 1:
            return Response(
                data={
                    "message": "Limit must be a positive integer"
                },
                status=status.HTTP_422_UNPROCESSABLE_ENTITY
            )
        if limit >= (n_topics - offset):
            limit = n_topics - offset

    target_n_terms = request.GET.get("nTerms", None)
    if target_n_terms:
        try:
            n_terms = int(target_n_terms)
        except ValueError:
            return Response(
                data={
                    "message": "Maximum number of terms must be a positive integer greater than 0"
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        if n_terms < 1:
            return Response(
                data={
                    "message": "Maximum number of terms must be a positive integer greater than 0"
                },
                status=status.HTTP_422_UNPROCESSABLE_ENTITY
            )

    data = dict()
    topics = queries.get_topics_terms_representation(
        model,
        *(topic,) if topic else tuple(range(offset, offset + limit)),
        n_terms=n_terms
    )

    if len(topics) > 0:
        data = {
            "name": model.name,
            "description": model.description,
            "training_context": model.training_context,
            "topics": topics
        }
        if (target_offset or target_limit) and not target_topic:
            data['meta'] = {
                'offset': offset,
                'limit': limit
            }
        if n_terms:
            data["meta"]["n_terms"] = n_terms
    else:
        return Response(
            data={
                "message": "Query returned no results"
            },
            status=404
        )
    return Response(data=data, status=200)


@api_view()
def models(request):
    return Response(queries.get_models())


@api_view(http_method_names=["POST"])
def analyze_text(request):
    text = request.data.get("text")
    model_name = request.data.get("model_name", None)
    result = lda_query.analyze_text(text, model_name)
    return Response(result)


@api_view()
def topic_evolution(request):
    model = request.GET.get("name", None)
    topic = int(request.GET.get("topic", -1))
    evolution = queries.get_topic_evolution(model, topic)
    result = {
        "model": model,
        "topic": topic,
        "model0_description": evolution["model0_description"],
        "model1_description": evolution["model1_description"],
        "parents": evolution["parents"]
    }
    return Response(result)

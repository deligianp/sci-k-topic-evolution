from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from resources import lda_query
from topic_evolution_visualization import queries


class RequestError(Exception):
    def __init__(self, message, error_code=status.HTTP_400_BAD_REQUEST):
        super(RequestError, self).__init__(f'HTTP {status}: {message}')
        self.message = message
        self.error_code = error_code


class RequestParseError(RequestError):
    pass


def parse_topic_preferred_representation(request):
    target_preferred_representation = request.GET.get('preferKeyphrase', None)
    topic_preferred_representation = None
    if target_preferred_representation is not None:
        target_preferred_representation = target_preferred_representation.strip()
        if not target_preferred_representation:
            raise RequestParseError('"preferKeyphrase" must be either "available" or "all"')
        elif target_preferred_representation not in ('all', 'available'):
            raise RequestParseError('"preferKeyphrase" must be either "available" or "all"')
        topic_preferred_representation = target_preferred_representation
    return topic_preferred_representation


def parse_model(request):
    target_model_name = request.GET.get("name", None)
    model = None
    if target_model_name is not None:
        target_model_name = target_model_name.strip()
        if target_model_name:
            model = queries.get_model(name=target_model_name)
            if not model:
                raise RequestParseError(
                    'Requested model "{}" does not exist'.format(target_model_name),
                    error_code=status.HTTP_404_NOT_FOUND
                )
        else:
            raise RequestParseError('Name of the model cannot be empty')
    return model


def parse_topic_range_offset(request, model, n_topics):
    target_offset = request.GET.get('offset', None)
    offset = None
    # If no specific topic is requested, then examine whether a range of topics are requested
    if target_offset is not None:
        target_offset = target_offset.strip()
        if target_offset:
            try:
                # Attempt to retrieve the potential offset definition. If no offset is defined, assume an offset of 0
                # (start from the very first topic)
                offset = int(target_offset)
            except ValueError:
                # In case an offset is defined but it is not a topic index, then an error is raised
                raise RequestParseError('Offset must be a positive integer or 0')
            if offset < 0:
                raise RequestParseError('Offset must be a positive integer or 0',
                                        error_code=status.HTTP_422_UNPROCESSABLE_ENTITY)
            elif offset >= n_topics:
                raise RequestParseError('Offset exceeds the total number of topics of model "{}"'.format(model.name),
                                        error_code=status.HTTP_404_NOT_FOUND)
        else:
            raise RequestParseError('Offset definition cannot be empty')
    return offset


def parse_topic_range_limit(request, max_limit):
    target_limit = request.GET.get('limit', None)
    limit = None
    if target_limit is not None:
        target_limit = target_limit.strip()
        if target_limit:
            try:
                limit = int(target_limit)
            except ValueError:
                raise RequestParseError('Limit must be a positive integer')
            if limit < 1:
                raise RequestParseError('Limit must be a positive integer',
                                        error_code=status.HTTP_422_UNPROCESSABLE_ENTITY)
            if limit > max_limit:
                limit = max_limit
        else:
            raise RequestParseError('Limit definition cannot be empty')
    return limit


def parse_topic(request, model, n_topics):
    target_topic = request.GET.get("topic", None)
    topic = None
    if target_topic is not None:
        target_topic = target_topic.strip()
        if target_topic:
            try:
                topic = int(target_topic)
                if topic < 0:
                    raise RequestParseError('Requested topic index must be a positive integer or 0',
                                            error_code=status.HTTP_422_UNPROCESSABLE_ENTITY)
                elif topic >= n_topics:
                    raise RequestParseError('Requested topic does not exist in model "{}"'.format(model.name),
                                            error_code=status.HTTP_404_NOT_FOUND)
            except ValueError:
                topic = target_topic
        else:
            raise RequestParseError('Requested topic index must be a positive integer or 0')
    return topic


def parse_topic_n_terms(request):
    target_n_terms = request.GET.get("nTerms", None)
    n_terms = None
    if target_n_terms is not None:
        target_n_terms = target_n_terms.strip()
        if target_n_terms:
            try:
                n_terms = int(target_n_terms)
            except ValueError:
                raise RequestParseError('Maximum number of terms must be a positive integer greater than 0')
            if n_terms < 1:
                raise RequestParseError('Maximum number of terms must be a positive integer greater than 0',
                                        error_code=status.HTTP_422_UNPROCESSABLE_ENTITY)
        else:
            raise RequestParseError('nTerms definition cannot be empty')
    return n_terms


@api_view()
def model_topics(request):
    try:
        model = parse_model(request)
        if not model:
            raise RequestError('Request must provide the name of the model, to which the target topics relate to')
        n_terms = parse_topic_n_terms(request)
        topic_preferred_representation = parse_topic_preferred_representation(request)
        n_topics = queries.get_number_of_topics(model)
        topic = parse_topic(request, model, n_topics)
        meta = dict()
        if not topic:
            defined_offset = parse_topic_range_offset(request, model, n_topics)
            offset = defined_offset or 0
            max_limit = n_topics - offset
            defined_limit = parse_topic_range_limit(request, max_limit)
            limit = defined_limit or max_limit
            topics = queries.get_topics_terms_representation(
                model,
                *tuple(range(offset, offset + limit)),
                n_terms=n_terms,
                topic_keyphrases=topic_preferred_representation
            )
            if defined_limit or defined_offset:
                meta['offset'] = offset
                meta['limit'] = limit
        else:
            topics = queries.get_topics_terms_representation(model, topic, n_terms=n_terms,
                                                             topic_keyphrases=topic_preferred_representation)
        if len(topics) > 0:
            data = {
                "name": model.name,
                "topics": topics
            }
            if meta:
                data['meta'] = meta
        else:
            raise RequestError('No topics available for given parameters', error_code=status.HTTP_404_NOT_FOUND)
        return Response(data=data, status=200)
    except RequestError as rpe:
        return Response(
            data={
                'message': rpe.message
            },
            status=rpe.error_code
        )


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


@api_view()
def model_novel_topics(request):
    try:
        model = parse_model(request)
        if not model:
            raise RequestError('Request must provide the name of the model to which the novel topics belong')
        topic_preferred_representation = parse_topic_preferred_representation(request)
        novel_topics = queries.get_novel_topics(model, topic_keyphrases=topic_preferred_representation)
        if len(novel_topics)>0:
            data={
                'model': model.name,
                'novelTopics': novel_topics
            }
        else:
            raise RequestError('No topics available for given parameters', error_code=status.HTTP_404_NOT_FOUND)
        return Response(data=data, status=200)
    except RequestError as rpe:
        return Response(
            data={
                'message': rpe.message
            },
            status=rpe.error_code
        )
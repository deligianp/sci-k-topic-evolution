from django.db.models import Q, F, Max

from topic_evolution import settings
from .models import Topic, LdaModel, Comparison, TopicsComparison


def get_model(name=None):
    if name:
        return LdaModel.objects.filter(name=name).first()
    return LdaModel.objects.filter(is_main=True)[:1].union(LdaModel.objects.all().order_by("pk")[:1]).first()


def get_number_of_topics(model):
    return Topic.objects.filter(parent_model=model).count()


def get_model_novel_topics(model):
    return (topic['topic_idx'] for topic in TopicsComparison.objects.filter(
        topic_1__parent_model=model
    ).values(
        'topic_1__index'
    ).annotate(
        max_similarity=Max('value'),
        topic_idx=F('topic_1__index')
    ).filter(
        max_similarity__lt=settings.SIMILARITY_THRESHOLD
    ).values(
        'topic_idx'
    )
            )


def get_topics_terms_representation(parent_model, *topics, n_terms=None, topic_keyphrases=None):
    result = dict()
    if not topics:
        # Get all terms available for all topics in the given model
        query_result = Topic.objects.filter(
            Q(topictermdistribution__term__original_word__rank=1) |
            Q(topictermdistribution__term__original_word__isnull=True),
            parent_model=parent_model,
        ).annotate(
            topic=F("index"),
            term=F("topictermdistribution__term__string"),
            word=F("topictermdistribution__term__original_word__string"),
            value=F("topictermdistribution__value")
        ).order_by(
            "index",
            "-value"
        ).values("topic", "keyphrase", "term", "word", "value")

        keyphrase_representation = False
        if topic_keyphrases == 'all':
            keyphrase_representation = not any(row['keyphrase'].strip() == '' for row in query_result)
        elif topic_keyphrases == 'available':
            keyphrase_representation = True

        for topic_term in query_result:
            if keyphrase_representation:
                topic = topic_term["keyphrase"] or topic_term["topic"]
            else:
                topic = topic_term['topic']

            if topic not in result:
                result[topic] = [
                    {"term": topic_term["term"] or topic_term["word"], "value": topic_term["value"]}
                ]
            else:
                if n_terms and len(result[topic]) >= n_terms:
                    continue
                result[topic].append(
                    {"term": topic_term["term"] or topic_term["word"], "value": topic_term["value"]}
                )

        for topic in result:
            result[topic] = sorted(result[topic], key=lambda td: td["value"], reverse=False)

    else:
        topic_results = list()
        # Get all terms for the topics defined in list argument `topics`
        for target_topic in topics:
            if type(target_topic) is str:
                query_result = Topic.objects.filter(
                    Q(topictermdistribution__term__original_word__rank=1) |
                    Q(topictermdistribution__term__original_word__isnull=True),
                    parent_model=parent_model,
                    keyphrase=target_topic
                ).annotate(
                    topic=F('index'),
                    term=F("topictermdistribution__term__string"),
                    word=F("topictermdistribution__term__original_word__string"),
                    value=F("topictermdistribution__value")
                ).order_by(
                    "index",
                    "-value"
                ).values('topic', 'keyphrase', "term", "word", "value")
            else:
                query_result = Topic.objects.filter(
                    Q(topictermdistribution__term__original_word__rank=1) |
                    Q(topictermdistribution__term__original_word__isnull=True),
                    parent_model=parent_model,
                    index=target_topic
                ).annotate(
                    topic=F('index'),
                    term=F("topictermdistribution__term__string"),
                    word=F("topictermdistribution__term__original_word__string"),
                    value=F("topictermdistribution__value")
                ).order_by(
                    "index",
                    "-value"
                ).values('topic', 'keyphrase', "term", "word", "value")

            if n_terms:
                query_result = query_result[:n_terms]
            topic_results.append(query_result)
        keyphrase_representation = False
        if topic_keyphrases == 'all':
            keyphrase_representation = not any(topic[0]['keyphrase'].strip() == '' for topic in topic_results)
        elif topic_keyphrases == 'available':
            keyphrase_representation = True
        for result_idx in range(len(topic_results)):
            if len(topic_results[result_idx]) > 0:
                if keyphrase_representation:
                    topic = topic_results[result_idx][0]['keyphrase'] or topic_results[result_idx][0]['topic']
                else:
                    topic = topics[result_idx]
                result[topic] = [
                    {"term": res["term"] or res["word"], "value": res["value"]}
                    for res in topic_results[result_idx]
                ]
    return result


def get_models():
    return LdaModel.objects.all().values("name", "description", "training_context")


def get_topic_evolution(model, topic):
    lda_model = LdaModel.objects.get(name=model)
    comparison = Comparison.objects.filter(Q(lda_model_0=lda_model) | Q(lda_model_1=lda_model)).first()
    if comparison.lda_model_0 == lda_model:
        # other_model = LdaModel.objects.get(id=comparison.lda_model_1).name
        other_model = comparison.lda_model_1.name
        topics_comparisons = TopicsComparison.objects.filter(
            parent_comparison=comparison,
            topic_0__parent_model=lda_model,
            topic_0__index=topic,
            value__gte=0.1
        ).values("topic_1__index", "value")
        model0_description = lda_model.description
        model1_description = comparison.lda_model_1.description

        return {
            "model0_description": model0_description,
            "model1_description": model1_description,
            "parents": [
                {
                    "name": "topic-{}".format(topic),
                    "topic": topic,
                    "modelName": model,
                    "highlight": True,
                    "associations": [
                        {
                            "child": {
                                "name": "topic-{}".format(edge["topic_1__index"]),
                                "highlight": False,
                                "topic": edge["topic_1__index"],
                                "modelName": other_model
                            },
                            "label": edge["value"]
                        } for edge in topics_comparisons
                    ]
                }
            ]
        }
    else:
        # other_model = LdaModel.objects.get(id=comparison.lda_model_0).name
        other_model = comparison.lda_model_0.name
        topics_comparisons = TopicsComparison.objects.filter(
            parent_comparison=comparison,
            topic_1__parent_model=lda_model,
            topic_1__index=topic,
            value__gte=0.1
        ).values("topic_0__index", "topic_1__index", "value")

        model0_description = lda_model.description
        model1_description = comparison.lda_model_1.description
        return {
            "model0_description": model0_description,
            "model1_description": model1_description,
            "parents": [
                {
                    "name": "topic-{}".format(edge["topic_0__index"]),
                    "topic": edge["topic_0__index"],
                    "modelName": other_model,
                    "highlight": False,
                    "associations": [
                        {
                            "child": {
                                "name": "topic-{}".format(topic),
                                "highlight": True,
                                "topic": topic,
                                "modelName": model
                            },
                            "label": edge["value"]}]
                } for edge in topics_comparisons
            ]
        }


def get_novel_topics(model, topic_keyphrases):
    result = list()
    novel_topics = TopicsComparison.objects.filter(topic_1__parent_model=model).values('topic_1__index',
                                                                                       'topic_1__keyphrase').annotate(
        max_sim=Max('value')).filter(max_sim__lt=settings.SIMILARITY_THRESHOLD).values('topic_1__index',
                                                                                       'topic_1__keyphrase')

    keyphrase_representation = False
    if topic_keyphrases == 'all':
        keyphrase_representation = not any(topic['topic_1__keyphrase'].strip() == '' for topic in novel_topics)
    elif topic_keyphrases == 'available':
        keyphrase_representation = True
    for topic in novel_topics:
        if keyphrase_representation:
            result.append(topic['topic_1__keyphrase'] or topic['topic_1__index'])
        else:
            result.append(topic['topic_1__index'])
    return result

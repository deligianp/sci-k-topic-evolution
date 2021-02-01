from django.db.models import Q, F

from .models import Topic, LdaModel, Comparison, TopicsComparison


def get_model(name=None):
    if name:
        return LdaModel.objects.filter(name=name).first()
    return LdaModel.objects.filter(is_main=True)[:1].union(LdaModel.objects.all().order_by("pk")[:1]).first()


def get_topics_terms_representation(parent_model, *topics):
    result = dict()
    if not topics:
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

        for topic_term in query_result:
            topic = topic_term["keyphrase"] or topic_term["topic"]
            # term_distribution = (topic_term["term"] or topic_term["word"], topic_term["value"])
            if topic not in result:
                result[topic] = [
                    {"term": topic_term["term"] or topic_term["word"], "value": topic_term["value"]}
                ]
            else:
                result[topic].append(
                    {"term": topic_term["term"] or topic_term["word"], "value": topic_term["value"]}
                )

        for topic in result:
            result[topic] = sorted(result[topic], key=lambda td: td["value"], reverse=False)

    else:
        for target_topic in topics:
            if type(target_topic) is str:
                query_result = Topic.objects.filter(
                    Q(topictermdistribution__term__original_word__rank=1) |
                    Q(topictermdistribution__term__original_word__isnull=True),
                    parent_model=parent_model,
                    keyphrase=target_topic
                ).annotate(
                    term=F("topictermdistribution__term__string"),
                    word=F("topictermdistribution__term__original_word__string"),
                    value=F("topictermdistribution__value")
                ).order_by(
                    "index",
                    "-value"
                ).values("term", "word", "value")
            else:
                query_result = Topic.objects.filter(
                    Q(topictermdistribution__term__original_word__rank=1) |
                    Q(topictermdistribution__term__original_word__isnull=True),
                    parent_model=parent_model,
                    index=target_topic
                ).annotate(
                    term=F("topictermdistribution__term__string"),
                    word=F("topictermdistribution__term__original_word__string"),
                    value=F("topictermdistribution__value")
                ).order_by(
                    "index",
                    "-value"
                ).values("term", "word", "value")
            if len(query_result) > 0:
                result[target_topic] = [
                    {"term": res["term"] or res["word"], "value": res["value"]}
                    for res in query_result
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

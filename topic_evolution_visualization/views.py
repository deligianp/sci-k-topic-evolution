import re

from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import Min, Max, Subquery
from django.http import JsonResponse, Http404
from django.shortcuts import render

from topic_evolution_visualization import models
from . import queries
from .forms import NewArticleForm


# Create your views here.
def home(request):
    template_context = dict()
    main_model = queries.get_model()
    if main_model:
        template_context["model"] = {
            "description": main_model.description,
            "training_context": main_model.training_context
        }
        template_context["topics"] = queries.get_topics_terms_representation(main_model)

    return render(context=template_context, template_name='topic_evolution_visualization/home.html', request=request)


# def topic_evolution(request):
#     navbar_json = generate_navbar(config.NAV_BAR_ADDRESSES, {"m_topic_evo"})
#     template_context = dict()
#     template_context["navbar"] = navbar_json
#     stored_comparisons = {row["name"]: row for row in
#                           models.Comparison.objects.values("name", "description", "type_of_comparison", "lower_bound",
#                                                            "upper_bound").annotate(
#                               min_topic_index=Min("topics_measurement__topic_1__index")).annotate(
#                               max_topic_index=Max("topics_measurement__topic_1__index"))}
#     template_context['ws_required'] = {"evolutions": list(stored_comparisons.values())}
#     if request.method == 'GET':
#         form_submitted = request.GET.get('submit', "") == "submit"
#         if form_submitted:
#             selected_comparison = request.GET.get("selected_metric", "")
#
#             # TODO: move to django.forms equivalent implementation
#             try:
#                 target_threshold = float(request.GET.get("threshold_value", None))
#                 if not stored_comparisons[selected_comparison]["lower_bound"] < target_threshold < \
#                        stored_comparisons[selected_comparison]["upper_bound"]:
#                     raise ValueError
#             except ValueError:
#                 template_context["server_error"] = True
#                 template_context["alert_title"] = "Invalid threshold for chosen distance model"
#                 template_context[
#                     "alert_message"] = "For distance model \"{}\": {} ≤ threshold ≤ {}, threshold: real number".format(
#                     stored_comparisons[selected_comparison]["description"],
#                     stored_comparisons[selected_comparison]["lower_bound"],
#                     stored_comparisons[selected_comparison]["upper_bound"])
#                 return render(context=template_context, template_name='topic-evolution.html', request=request)
#             except TypeError:
#                 template_context["server_error"] = True
#                 template_context["alert_title"] = "Invalid threshold for chosen distance model"
#                 template_context["alert_message"] = "Threshold must be a number"
#                 return render(context=template_context, template_name='topic-evolution.html', request=request)
#
#             try:
#                 topic_id = int(request.GET.get("topic_id", None))
#                 if not stored_comparisons[selected_comparison]["min_topic_index"] < topic_id < \
#                        stored_comparisons[selected_comparison]["max_topic_index"]:
#                     raise ValueError
#             except ValueError:
#                 template_context["server_error"] = True
#                 template_context["alert_title"] = "Invalid topic index for chosen distance model"
#                 template_context[
#                     "alert_message"] = "For distance model \"{}\": {} ≤ topic index ≤ {}, topic index: natural number".format(
#                     stored_comparisons[selected_comparison]["description"],
#                     stored_comparisons[selected_comparison]["min_topic_index"],
#                     stored_comparisons[selected_comparison]["max_topic_index"])
#                 return render(context=template_context, template_name='topic-evolution.html', request=request)
#             except TypeError:
#                 template_context["server_error"] = True
#                 template_context["alert_title"] = "Invalid topic index for chosen distance model"
#                 template_context["alert_message"] = "Topic index must be a number"
#                 return render(context=template_context, template_name='topic-evolution.html', request=request)
#                 # ========================================================
#
#             if stored_comparisons[selected_comparison]["type_of_comparison"] == 0:
#                 edges = models.TopicsComparison.objects.filter(
#                     topic_0__in=Subquery(
#                         models.TopicsComparison.objects.filter(
#                             parent_comparison__name=selected_comparison,
#                             topic_1__index=topic_id,
#                             value__gte=target_threshold
#                         ).values("topic_0")),
#                     value__gte=target_threshold,
#                     parent_comparison__name=selected_comparison).values(
#                     "parent_comparison__description",
#                     "parent_comparison__lda_model_0__name",
#                     "parent_comparison__lda_model_0__training_context",
#                     "parent_comparison__lda_model_0__description",
#                     "parent_comparison__lda_model_1__name",
#                     "parent_comparison__lda_model_1__training_context",
#                     "parent_comparison__lda_model_1__description",
#                     "topic_0__index",
#                     "topic_1__index",
#                     "value"
#                 )
#             else:
#                 edges = models.TopicsComparison.objects.filter(
#                     topic_0__in=Subquery(
#                         models.TopicsComparison.objects.filter(
#                             parent_comparison__name=selected_comparison,
#                             topic_1__index=topic_id,
#                             value__lte=target_threshold
#                         ).values("topic_0")),
#                     value__lte=target_threshold,
#                     parent_comparison__name=selected_comparison).values(
#                     "parent_comparison__description",
#                     "parent_comparison__lda_model_0__name",
#                     "parent_comparison__lda_model_0__training_context",
#                     "parent_comparison__lda_model_0__description",
#                     "parent_comparison__lda_model_1__name",
#                     "parent_comparison__lda_model_1__description",
#                     "parent_comparison__lda_model_1__training_context",
#                     "topic_0__index",
#                     "topic_1__index",
#                     "value"
#                 )
#             if len(edges) == 0:
#                 template_context["server_error"] = True
#                 template_context["alert_title"] = "No topics for given threshold"
#                 template_context["alert_message"] = "Cannot infer any topic evolution for topic {}, satisfying the " \
#                                                     "{} threshold of {}".format(
#                     topic_id,
#                     "minimum" if stored_comparisons[selected_comparison]["type_of_comparison"] == 0 else "maximum",
#                     target_threshold)
#                 return render(context=template_context, template_name='topic-evolution.html', request=request)
#
#             # Normalize
#             normalized_result = dict()
#
#             template_context["visualization"] = dict()
#             template_context["visualization"]["data_description"] = dict()
#             template_context["visualization"]["data_description"]["comparison_description"] = edges[0][
#                 "parent_comparison__description"]
#             template_context["visualization"]["data_description"]["lda_model_0_description"] = edges[0][
#                 "parent_comparison__lda_model_0__description"]
#             template_context["visualization"]["data_description"]["lda_model_0_training_context"] = edges[0][
#                 "parent_comparison__lda_model_0__training_context"]
#             template_context["visualization"]["data_description"]["lda_model_1_description"] = edges[0][
#                 "parent_comparison__lda_model_1__description"]
#             template_context["visualization"]["data_description"]["lda_model_1_training_context"] = edges[0][
#                 "parent_comparison__lda_model_1__training_context"]
#             parents_dict = dict()
#             for row in edges:
#                 topic_0_index = row["topic_0__index"]
#                 topic_1_index = row["topic_1__index"]
#                 value = row["value"]
#
#                 if topic_0_index not in parents_dict:
#                     parents_dict[topic_0_index] = {
#                         "name": row["parent_comparison__lda_model_0__name"] + "_" + str(topic_0_index),
#                         "associations": list()
#                     }
#
#                 parents_dict[topic_0_index]["associations"].append(
#                     {
#                         "child": {
#                             "name": row["parent_comparison__lda_model_1__name"] + "_" + str(topic_1_index),
#                             "highlight": topic_1_index == topic_id
#                         },
#                         "label": value
#                     }
#                 )
#
#             import json
#             template_context["visualization"]["data"] = json.dumps(tuple(parents_dict.values()))
#     return render(context=template_context, template_name='topic-evolution.html', request=request)
#
#
# def ajax_topic_evolution(request, *args, **kwargs):
#     if request.method == "POST":
#         if "topic_index" in kwargs and "measure_name" in request.POST and "threshold" in request.POST:
#             topic_index = int(kwargs["topic_index"])
#             measure_name = request.POST["measure_name"]
#             threshold = float(request.POST["threshold"])
#             relative_comparison = models.Comparison.objects.get(name=measure_name)
#             if relative_comparison.type_of_comparison == 0:
#                 result = models.TopicsComparison.objects.filter(
#                     topic_0__in=Subquery(
#                         models.TopicsComparison.objects.filter(
#                             topic_1__index=topic_index,
#                             parent_comparison__lda_model_1__name=config.CONFIG_VALUES["MAIN_LDA_MODEL_NAME"],
#                             parent_comparison__name=measure_name,
#                             value__gte=threshold
#                         ) \
#                             .order_by("-value") \
#                             .values("topic_0")[:4]),
#                     parent_comparison__name=measure_name,
#                     value__gte=threshold
#                 ).values(
#                     "topic_0__index",
#                     "topic_1__index",
#                     "parent_comparison__lda_model_0__name",
#                     "parent_comparison__lda_model_1__name",
#                     "parent_comparison__lda_model_0__description",
#                     "parent_comparison__lda_model_1__description",
#                     "value"
#                 )
#             else:
#                 result = models.TopicsComparison.objects.filter(
#                     topic_0__in=Subquery(
#                         models.TopicsComparison.objects.filter(
#                             topic_1__index=topic_index,
#                             parent_comparison__lda_model_1__name=config.CONFIG_VALUES["MAIN_LDA_MODEL_NAME"],
#                             parent_comparison__name=measure_name,
#                             value__lte=threshold
#                         ) \
#                             .order_by("value") \
#                             .values("topic_0")[:4]),
#                     parent_comparison__name=measure_name,
#                     value__lte=threshold
#                 ).values(
#                     "topic_0__index",
#                     "topic_1__index",
#                     "parent_comparison__lda_model_0__name",
#                     "parent_comparison__lda_model_1__name",
#                     "parent_comparison__lda_model_0__description",
#                     "parent_comparison__lda_model_1__description",
#                     "value"
#                 )
#             parents = dict()
#             children = dict()
#             for edge in result:
#                 parent_name = edge["parent_comparison__lda_model_0__name"] + "_" + str(edge["topic_0__index"])
#                 child_name = edge["parent_comparison__lda_model_1__name"] + "_" + str(edge["topic_1__index"])
#                 if parent_name in parents:
#                     parent = parents[parent_name]
#                 else:
#                     parent = {
#                         "name": parent_name,
#                         "associations": []
#                     }
#                     parents[parent_name] = parent
#
#                 if child_name in children:
#                     child = children[child_name]
#                 else:
#                     child = {
#                         "name": child_name,
#                         "highlight": edge["topic_1__index"] == topic_index
#                     }
#                     children[child_name] = child
#                 parent["associations"].append({"child": child, "label": edge["value"]})
#             return JsonResponse({"parents": [parents[parent] for parent in parents]})
#
#
# def ajax_get_topic_terms(request, *args, **kwargs):
#     target_topic_description = request.POST.get("topic_description", None)
#     topic_terms = list()
#     if target_topic_description is not None:
#         parent_model_name, topic_index = re.match(r"^([A-Za-z0-9_\-\.]+)_([0-9]+)$", target_topic_description).groups()
#         top_10_terms = models.Term.objects.filter(parent_topics__index=topic_index,
#                                                   parent_topics__parent_model__name=parent_model_name
#                                                   ) \
#                            .order_by("-topictermdistribution__value") \
#                            .values("string")[:10] \
#             .annotate(non_stemmed=ArrayAgg("original_word__string"))
#         for term_dict in top_10_terms:
#             if term_dict["non_stemmed"] != [None]:
#                 topic_terms.append(", ".join(term_dict["non_stemmed"][:3]))
#             else:
#                 topic_terms.append(term_dict["string"])
#         return JsonResponse({"terms": topic_terms})
#     return JsonResponse({"terms": None})
#
#
# def topic_show(request, *args, **kwargs):
#     try:
#         topic_index = int(kwargs.get("topic_index"))
#     except Exception:
#         return Http404
#     template_context = dict()
#     template_context["topic_index"] = topic_index
#     navbar_json = generate_navbar(config.NAV_BAR_ADDRESSES, {})
#     template_context["navbar"] = navbar_json
#
#     top_n_terms = models.Term.objects.filter(parent_topics__index=topic_index,
#                                              parent_topics__parent_model__name=config.CONFIG_VALUES[
#                                                  "MAIN_LDA_MODEL_NAME"]).order_by(
#         "-topictermdistribution__value").values("topictermdistribution__value", "string").annotate(
#         words=ArrayAgg("original_word__string"))[:config.CONFIG_VALUES["TOP_N_TOPIC_TERMS_TO_PRINT"]]
#     result = list()
#     for term in top_n_terms:
#         if len(term["words"]) > 0:
#             result.append({
#                 "term": ", ".join(term["words"]),
#                 "value": round(100 * term["topictermdistribution__value"], 2)})
#
#     available_comparisons = models.Comparison.objects.filter(
#         lda_model_1__name=config.CONFIG_VALUES["MAIN_LDA_MODEL_NAME"]).values("name",
#                                                                               "lower_bound",
#                                                                               "upper_bound",
#                                                                               "type_of_comparison",
#                                                                               "description",
#                                                                               "lda_model_0__description",
#                                                                               "lda_model_1__description",
#                                                                               "type_of_comparison")
#     evolutions = list()
#     for available_comparison in available_comparisons:
#         evolution = dict()
#         evolution["name"] = available_comparison["name"]
#         evolution["description"] = available_comparison["description"]
#         evolution["lower_bound"] = float(available_comparison["lower_bound"])
#         evolution["upper_bound"] = float(available_comparison["upper_bound"])
#         evolution["is_score"] = "true " if available_comparison["type_of_comparison"] == 0 else "false"
#         evolution["lda_model_0"] = available_comparison["lda_model_0__description"]
#         evolution["lda_model_1"] = available_comparison["lda_model_1__description"]
#         evolutions.append(evolution)
#     template_context["topic_terms"] = result
#     template_context["evolutions"] = evolutions
#
#     return render(context=template_context, template_name='p_topic.html', request=request)
#
#
# def new_article_topic_analysis(request):
#     navbar_json = generate_navbar(config.NAV_BAR_ADDRESSES, {"new_article"})
#     template_context = dict()
#     template_context["navbar"] = navbar_json
#     if request.method == "POST":
#         new_article_form = NewArticleForm(request.POST)
#         if new_article_form.is_valid():
#             article_text = new_article_form.cleaned_data["article_text_field"]
#             article_additional_info = {
#                 "article_additional_info": [
#                     {
#                         "text_row": True,
#                         "heading": "Text",
#                         "content": article_text
#                     }
#                 ]
#             }
#             template_context["text_info"] = article_additional_info
#             template_context["target_text"] = article_text
#     else:
#         new_article_form = NewArticleForm()
#     template_context["new_article_form"] = new_article_form
#     return render(request, template_name='p_new_article.html', context=template_context)
#
#
# def ajax_text_topics(request):
#     if request.method == "POST":
#         text = request.POST.get("text", None)
#         if text is not None:
#             try:
#                 top_n_article_topics = lda_query.analyze_text(text)
#             except lda_query.PreprocessingError as pe:
#                 result = {
#                     "error": {
#                         "title": "Preprocessing error",
#                         "message": str(pe)
#                     }
#                 }
#                 return JsonResponse(result)
#             result = {
#                 "result": [{"topic": topic_distribution[0], "value": topic_distribution[1]}
#                            for topic_distribution in top_n_article_topics]
#             }
#             return JsonResponse(result)
#         return JsonResponse(status=500)
#     raise Http404

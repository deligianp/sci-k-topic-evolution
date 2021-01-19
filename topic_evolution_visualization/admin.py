import os

from django.contrib import admin
from django.db import transaction
from gensim import models

from topic_evolution import settings
from .models import LdaModel, Topic, Term, TopicTermDistribution


@admin.register(LdaModel)
class LdaModelAdmin(admin.ModelAdmin):

    def save_related(self, request, form, formsets, change):
        path = os.path.abspath(request.POST["path"])
        lda_model = models.LdaModel.load(path)
        dictionary = lda_model.id2word

        lda_model_obj = LdaModel.objects.get(name=request.POST["name"])
        with transaction.atomic():
            topics = list()
            topicterm_distribution_matrix = list()
            for i in range(lda_model.num_topics):
                topics.append(Topic(index=i, parent_model=lda_model_obj, keyphrase=""))
                topicterm_distribution_matrix.append(lda_model.get_topic_terms(i, topn=settings.TOP_N_TOPIC_TERMS))

            Topic.objects.bulk_create(topics)

            with transaction.atomic():
                terms = dict()
                topicterm_distributions = list()
                for topic_index in range(len(topicterm_distribution_matrix)):
                    topicterms_distribution = topicterm_distribution_matrix[topic_index]
                    for rank in range(len(topicterms_distribution)):
                        term_id = int(topicterms_distribution[rank][0])
                        term_weight = float(topicterms_distribution[rank][1])
                        term_string = dictionary[term_id]
                        if term_id not in terms:
                            terms[term_id] = Term.objects.get_or_create(string=term_string)
                        topicterm_distributions.append(
                            TopicTermDistribution(topic=topics[topic_index], term=terms[term_id][0],
                                                  value=round(term_weight, 5),
                                                  rank=rank + 1))
                # Term.objects.bulk_create([new_term[0] for new_term in filter(lambda v: v[1] == 1, terms.values())])
                TopicTermDistribution.objects.bulk_create(topicterm_distributions)

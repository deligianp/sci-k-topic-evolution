import os

import numpy as np
from django.db import transaction
from django.utils.text import slugify

from topic_evolution_visualization import models


def create(path, name, description, lower_bound, upper_bound, lda_model_old, lda_model_new, is_score=True):
    clean_path = os.path.abspath(os.path.expanduser(path))
    if not os.path.exists(clean_path):
        raise ValueError("Path to comparison file \"{}\" does not exist".format(path))
    clean_name = slugify(name)
    clean_description = description
    clean_is_score = (is_score is True)
    clean_upper_bound = float(upper_bound)
    clean_lower_bound = float(lower_bound)

    if clean_upper_bound < clean_lower_bound:
        raise ValueError(
            "Upper bound must be greater or at least equal to lower bound {}. Given upper bound: {}".format(
                clean_lower_bound, clean_upper_bound
            )
        )

    clean_old_lda_model = models.LdaModel.objects.get(name=lda_model_old)
    clean_new_lda_model = models.LdaModel.objects.get(name=lda_model_new)

    metric_matrix = np.load(clean_path)

    max_topic_0, max_topic_1 = metric_matrix.shape
    old_topics = models.Topic.objects.filter(parent_model=clean_old_lda_model)
    new_topics = models.Topic.objects.filter(parent_model=clean_new_lda_model)
    n_topics_0 = old_topics.count()
    n_topics_1 = new_topics.count()
    if max_topic_0 != n_topics_0:
        raise TypeError(
            "Topic matrix's number of rows, {}, does not match the number of topics registered to model {}, with {} "
            "topics".format(max_topic_0, clean_old_lda_model.name, n_topics_0))

    if max_topic_1 != n_topics_1:
        raise TypeError(
            "Topic matrix's number of rows, {}, does not match the number of topics registered to model {}, with {} "
            "topics".format(max_topic_1, clean_new_lda_model.name, n_topics_1))

    with transaction.atomic():
        comparison = models.Comparison(
            name=clean_name,
            description=clean_description,
            is_score=clean_is_score,
            lower_bound=clean_lower_bound,
            upper_bound=clean_upper_bound,
            lda_model_0=clean_old_lda_model,
            lda_model_1=clean_new_lda_model
        )

        comparison.save()
        with transaction.atomic():
            topics_comparisons = list()
            old_topics_map = {
                topic.index: topic for topic in old_topics
            }
            new_topics_map = {
                topic.index: topic for topic in new_topics
            }
            for i in old_topics_map:
                for j in new_topics_map:
                    topics_comparisons.append(models.TopicsComparison(
                        parent_comparison=comparison,
                        topic_0=old_topics_map[i],
                        topic_1=new_topics_map[j],
                        value=float(metric_matrix[i][j])
                    ))
            models.TopicsComparison.objects.bulk_create(topics_comparisons)

from rest_framework import test, status

from topic_evolution_visualization.models import LdaModel, Topic, Term, TopicTermDistribution, Comparison, \
    TopicsComparison


def meta_exist(data, offset, limit=None):
    rules = [
        lambda d, o, l: 'meta' in d,
        lambda d, o, l: 'offset' in d['meta'],
        lambda d, o, l: d['meta']['offset'] == o,
        lambda d, o, l: not l or (l and 'limit' in d['meta']),
        lambda d, o, l: not l or (l and d['meta']['limit'] == l)
    ]
    return all(check(data, offset, limit) for check in rules)


def topics_exist(data, *topics):
    rules = [
        lambda d, *ts: 'topics' in d,
        lambda d, *ts: len(set(d['topics']).difference(set(ts))) == 0
    ]
    return all(check(data, *topics) for check in rules)


def n_terms_exist(data, n_terms):
    rules = [
        lambda d, n: 'topics' in d,
        lambda d, n: all(len(d['topics'][t]) == n for t in d['topics'])
    ]
    return all(check(data, n_terms) for check in rules)


class TestModelTopicsEndpointCase(test.APITestCase):

    def setUp(self):
        self.url = '/backend/api/model-topics'
        self.model_name = 'test-name'
        self.n_topics = 3
        self.n_terms = 3
        model = LdaModel.objects.create(
            name=self.model_name,
            description='',
            is_main=True,
            path='/',
            training_context='',
            preprocessor_name='',
            use_tfidf=True
        )
        topic0 = Topic.objects.create(parent_model=model, index=0, keyphrase='')
        topic1 = Topic.objects.create(parent_model=model, index=1, keyphrase='topic-one')
        topic2 = Topic.objects.create(parent_model=model, index=2, keyphrase='')

        term0 = Term.objects.create(string='term0')
        term1 = Term.objects.create(string='term1')
        term2 = Term.objects.create(string='term2')
        TopicTermDistribution.objects.create(topic=topic0, term=term0, value=0.6, rank=1)
        TopicTermDistribution.objects.create(topic=topic0, term=term1, value=0.3, rank=2)
        TopicTermDistribution.objects.create(topic=topic0, term=term2, value=0.1, rank=3)
        TopicTermDistribution.objects.create(topic=topic1, term=term0, value=0.4, rank=1)
        TopicTermDistribution.objects.create(topic=topic1, term=term1, value=0.3, rank=2)
        TopicTermDistribution.objects.create(topic=topic1, term=term2, value=0.3, rank=3)
        TopicTermDistribution.objects.create(topic=topic2, term=term0, value=0.5, rank=1)
        TopicTermDistribution.objects.create(topic=topic2, term=term1, value=0.3, rank=2)
        TopicTermDistribution.objects.create(topic=topic2, term=term2, value=0.2, rank=3)

    def test_valid_model_name(self):
        response = self.client.get(
            f'{self.url}?name={self.model_name}'
        )
        self.assertEquals(response.status_code, status.HTTP_200_OK)

        self.assertEquals(response.data.get('name'), self.model_name)
        self.assertEquals(len(response.data.get('topics').keys()), self.n_topics)
        self.assertTrue('meta' not in response.data)

    def test_no_model_name(self):
        response = self.client.get(self.url)
        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue('message' in response.data)
        self.assertEquals(len(response.data), 1)

    def test_invalid_model_name(self):
        response = self.client.get(
            f'{self.url}?name=invalid'
        )
        self.assertEquals(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue('message' in response.data)
        self.assertEquals(len(response.data), 1)

    def test_empty_model_name(self):
        response = self.client.get(
            f'{self.url}?name= '
        )
        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue('message' in response.data)
        self.assertEquals(len(response.data), 1)

    def test_valid_topic_index(self):
        target_topic_idx = 1
        response = self.client.get(
            f'{self.url}?name={self.model_name}&topic={target_topic_idx}'
        )
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(len(response.data.get('topics')), 1)
        self.assertTrue(target_topic_idx in response.data.get('topics'))
        self.assertTrue('meta' not in response.data)

    def test_valid_topic_keyphrase(self):
        target_topic_keyphrase = 'topic-one'
        response = self.client.get(
            f'{self.url}?name={self.model_name}&topic={target_topic_keyphrase}'
        )
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(len(response.data.get('topics')), 1)
        self.assertTrue(target_topic_keyphrase in response.data.get('topics'))
        self.assertTrue('meta' not in response.data)

    def test_invalid_topic_index(self):
        response = self.client.get(
            f'{self.url}?name={self.model_name}&topic=-13'
        )
        self.assertEquals(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEquals(len(response.data), 1)
        self.assertTrue("message" in response.data)

    def test_non_existing_topic_keyphrase(self):
        target_topic_keyphrase = 'thirteen'
        response = self.client.get(
            f'{self.url}?name={self.model_name}&topic={target_topic_keyphrase}'
        )
        self.assertEquals(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEquals(len(response.data), 1)
        self.assertTrue('message' in response.data)

    #
    def test_non_existing_topic_index(self):
        target_topic_idx = 4
        response = self.client.get(
            f'{self.url}?name={self.model_name}&topic={target_topic_idx}'
        )
        self.assertEquals(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEquals(len(response.data), 1)
        self.assertTrue('message' in response.data)

    def test_empty_topic_index(self):
        response = self.client.get(
            f'{self.url}?name={self.model_name}&topic='
        )
        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEquals(len(response.data), 1)
        self.assertTrue("message" in response.data)

    def test_valid_topic_range(self):
        offset = 1
        limit = 2
        response = self.client.get(
            f'{self.url}?name={self.model_name}&offset={offset}&limit={limit}'
        )
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(len(response.data.get('topics')), limit)

        # Assert that all topics with index from [OFFSET] up to [OFFSET+LIMIT] exclusive, have been returned
        self.assertTrue(topics_exist(response.data, *(idx for idx in range(offset, offset + limit))))
        self.assertTrue(meta_exist(response.data, offset, limit))

    def test_valid_topic_range_defined_only_by_offset(self):
        offset = 1
        response = self.client.get(
            f'{self.url}?name={self.model_name}&offset={offset}'
        )
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(len(response.data.get('topics')), 2)

        # Assert that all topics with index from [OFFSET] up to [OFFSET+LIMIT] exclusive, have been returned
        self.assertTrue(topics_exist(response.data, *(idx for idx in range(offset, 3))))
        self.assertTrue(meta_exist(response.data, offset, self.n_topics - offset))

    def test_valid_topic_range_defined_only_by_limit(self):
        limit = 2
        response = self.client.get(
            f'{self.url}?name={self.model_name}&limit={limit}'
        )
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(len(response.data.get('topics')), limit)

        # Assert that the first [LIMIT] topics have been returned
        self.assertTrue(topics_exist(response.data, *(idx for idx in range(limit))))
        self.assertTrue(meta_exist(response.data, 0, limit))

    def test_valid_topic_range_of_size_1(self):
        offset = 1
        limit = 1
        response = self.client.get(
            f'{self.url}?name={self.model_name}&offset={offset}&limit={limit}'
        )
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(len(response.data.get('topics')), limit)

        # Assert that the first only topic [OFFSET] has been returned, as well as 'meta' info
        self.assertTrue(topics_exist(response.data, *(idx for idx in range(offset, offset + limit))))
        self.assertTrue(meta_exist(response.data, offset, limit))

    def test_topic_range_with_invalid_offset_number(self):
        offset = -10
        response = self.client.get(
            f'{self.url}?name={self.model_name}&offset={offset}'
        )

        self.assertEquals(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEquals(len(response.data), 1)
        self.assertTrue('message' in response.data)

    def test_topic_range_with_invalid_offset_type(self):
        offset = 'offset'
        response = self.client.get(
            f'{self.url}?name={self.model_name}&offset={offset}'
        )

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEquals(len(response.data), 1)
        self.assertTrue('message' in response.data)

    def test_topic_range_with_valid_non_existing_offset(self):
        offset = 3
        response = self.client.get(
            f'{self.url}?name={self.model_name}&offset={offset}'
        )

        self.assertEquals(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEquals(len(response.data), 1)
        self.assertTrue('message' in response.data)

    def test_topic_range_with_empty_offset(self):
        offset = '  '
        response = self.client.get(
            f'{self.url}?name={self.model_name}&offset={offset}'
        )

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEquals(len(response.data), 1)
        self.assertTrue('message' in response.data)

    def test_topic_range_with_invalid_limit_number(self):
        limit = 0
        response = self.client.get(
            f'{self.url}?name={self.model_name}&limit={limit}'
        )

        self.assertEquals(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEquals(len(response.data), 1)
        self.assertTrue('message' in response.data)

    def test_topic_range_with_invalid_limit_type(self):
        limit = 'limit'
        response = self.client.get(
            f'{self.url}?name={self.model_name}&limit={limit}'
        )

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEquals(len(response.data), 1)
        self.assertTrue('message' in response.data)

    def test_topic_range_with_empty_limit(self):
        limit = '   '
        response = self.client.get(
            f'{self.url}?name={self.model_name}&limit={limit}'
        )

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEquals(len(response.data), 1)
        self.assertTrue('message' in response.data)

    def test_topic_range_with_valid_overextending_limit(self):
        offset = 1
        limit = 324015
        response = self.client.get(
            f'{self.url}?name={self.model_name}&offset={offset}&limit={limit}'
        )

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(len(response.data.get('topics')), self.n_topics - offset)

        self.assertTrue(topics_exist(response.data, *(idx for idx in range(self.n_topics))))
        self.assertTrue(meta_exist(response.data, offset, self.n_topics - offset))

    def test_valid_nterms(self):
        offset = 1
        limit = 2
        n_terms = 2
        response = self.client.get(
            f'{self.url}?name={self.model_name}&offset={offset}&limit={limit}&nTerms={n_terms}'
        )

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(len(response.data.get('topics')), limit)

        self.assertTrue(topics_exist(response.data, *(idx for idx in range(offset, offset + limit))))
        self.assertTrue(n_terms_exist(response.data, n_terms))
        self.assertTrue(meta_exist(response.data, offset, self.n_topics - offset))

    def test_invalid_nterms_number(self):
        offset = 1
        limit = 2
        n_terms = 0
        response = self.client.get(
            f'{self.url}?name={self.model_name}&offset={offset}&limit={limit}&nTerms={n_terms}'
        )

        self.assertEquals(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEquals(len(response.data), 1)
        self.assertTrue('message' in response.data)

    def test_invalid_nterms_type(self):
        offset = 1
        limit = 2
        n_terms = 'n_terms'
        response = self.client.get(
            f'{self.url}?name={self.model_name}&offset={offset}&limit={limit}&nTerms={n_terms}'
        )

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEquals(len(response.data), 1)
        self.assertTrue('message' in response.data)

    def test_empty_nterms_type(self):
        offset = 1
        limit = 2
        n_terms = '    '
        response = self.client.get(
            f'{self.url}?name={self.model_name}&offset={offset}&limit={limit}&nTerms={n_terms}'
        )

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEquals(len(response.data), 1)
        self.assertTrue('message' in response.data)

    def test_overextending_nterms_number(self):
        offset = 1
        limit = 2
        n_terms = 31
        response = self.client.get(
            f'{self.url}?name={self.model_name}&offset={offset}&limit={limit}&nTerms={n_terms}'
        )

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(len(response.data.get('topics')), limit)
        self.assertTrue(topics_exist(response.data, *(idx for idx in range(offset, offset + limit))))
        self.assertTrue(n_terms_exist(response.data, self.n_terms))
        self.assertTrue(meta_exist(response.data, offset, self.n_topics - offset))

    def test_topic_prefer_keyphrase_available(self):
        response = self.client.get(
            f'{self.url}?name={self.model_name}&preferKeyphrase=available'
        )
        self.assertEquals(response.status_code, status.HTTP_200_OK)

        self.assertEquals(response.data.get('name'), self.model_name)
        self.assertEquals(len(response.data.get('topics').keys()), 3)
        self.assertTrue(topics_exist(response.data, 0, 'topic-one', 2))

    def test_topic_prefer_keyphrase_all(self):
        response = self.client.get(
            f'{self.url}?name={self.model_name}&preferKeyphrase=all'
        )
        self.assertEquals(response.status_code, status.HTTP_200_OK)

        self.assertEquals(response.data.get('name'), self.model_name)
        self.assertEquals(len(response.data.get('topics').keys()), 3)
        self.assertTrue(topics_exist(response.data, *list(range(3))))

    def test_topic_prefer_keyphrase_invalid(self):
        response = self.client.get(
            f'{self.url}?name={self.model_name}&preferKeyphrase=true'
        )
        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue('message' in response.data)
        self.assertEquals(len(response.data), 1)

    def test_topic_prefer_keyphrase_empty(self):
        response = self.client.get(
            f'{self.url}?name={self.model_name}&preferKeyphrase=      '
        )
        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue('message' in response.data)
        self.assertEquals(len(response.data), 1)

# class TestModelNovelTopicsEndpointCase(test.APITestCase):
#
#     def setUp(self):
#         self.url = '/backend/api/model-novel-topics'
#         self.model_name_0 = 'test-name-0'
#         self.model_name_1 = 'test-name-1'
#         model0 = LdaModel.objects.create(
#             name=self.model_name_0,
#             description='',
#             is_main=True,
#             path='/',
#             training_context='',
#             preprocessor_name='',
#             use_tfidf=True
#         )
#         model1 = LdaModel.objects.create(
#             name=self.model_name_1,
#             description='',
#             is_main=True,
#             path='/',
#             training_context='',
#             preprocessor_name='',
#             use_tfidf=True
#         )
#         topic00 = Topic.objects.create(parent_model=model0, index=0, keyphrase='')
#         topic01 = Topic.objects.create(parent_model=model0, index=1, keyphrase='topic-one')
#         topic10 = Topic.objects.create(parent_model=model1, index=0, keyphrase='t-zero')
#         topic11 = Topic.objects.create(parent_model=model1, index=1, keyphrase='t-one')
#         topic12 = Topic.objects.create(parent_model=model1, index=2, keyphrase='')
#         topic13 = Topic.objects.create(parent_model=model1, index=3, keyphrase='')
#
#         comparison = Comparison.objects.create(
#             name='mock',
#             description='mock',
#             is_score=True,
#             lower_bound=0,
#             upper_bound=1,
#             lda_model_0=model0,
#             lda_model_1=model1
#         )
#
#         topicsComparison00 = TopicsComparison.objects.create(
#             parent_comparison=comparison, topic_0=topic00, topic_1=topic10, value=0.05
#         )
#         topicsComparison10 = TopicsComparison.objects.create(
#             parent_comparison=comparison, topic_0=topic01, topic_1=topic10, value=0.15
#         )
#         topicsComparison01 = TopicsComparison.objects.create(
#             parent_comparison=comparison, topic_0=topic00, topic_1=topic11, value=0.05
#         )
#         topicsComparison11 = TopicsComparison.objects.create(
#             parent_comparison=comparison, topic_0=topic01, topic_1=topic11, value=0.05
#         )
#         topicsComparison02 = TopicsComparison.objects.create(
#             parent_comparison=comparison, topic_0=topic00, topic_1=topic12, value=0.05
#         )
#         topicsComparison12 = TopicsComparison.objects.create(
#             parent_comparison=comparison, topic_0=topic01, topic_1=topic12, value=0.05
#         )
#         topicsComparison03 = TopicsComparison.objects.create(
#             parent_comparison=comparison, topic_0=topic00, topic_1=topic13, value=0.05
#         )
#         topicsComparison13 = TopicsComparison.objects.create(
#             parent_comparison=comparison, topic_0=topic01, topic_1=topic13, value=0.15
#         )
#
#     def assertTopicExistence(self, data, *topics):
#         self.assertTrue('topics' in data)
#         returned_topics = set(data['topics'].keys())
#         expected_topics = set(topics)
#         self.assertEquals(len(returned_topics.difference(expected_topics)), 0)
#
#     def test_valid_model_name(self):
#         response = self.client.get(
#             f'{self.url}?name={self.model_name_1}'
#         )
#         self.assertEquals(response.status_code, status.HTTP_200_OK)
#
#         self.assertEquals(response.data.get('name'), self.model_name_1)
#         self.assertEquals(len(response.data.get('topics').keys()), 2)
#         self.assertTopicExistence(response.data, 0, 3)
#
#     def test_invalid_model_name(self):
#         response = self.client.get(
#             f'{self.url}?name=invalid'
#         )
#         self.assertEquals(response.status_code, status.HTTP_404_NOT_FOUND)
#         self.assertTrue('message' in response.data)
#         self.assertEquals(len(response.data), 1)
#
#     def test_no_model_name(self):
#         response = self.client.get(self.url)
#         self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
#         self.assertTrue('message' in response.data)
#         self.assertEquals(len(response.data), 1)
#
#     def test_topic_prefer_keyphrase_available(self):
#         response = self.client.get(
#             f'{self.url}?name={self.model_name_1}&preferKeyphrase=available'
#         )
#         self.assertEquals(response.status_code, status.HTTP_200_OK)
#
#         self.assertEquals(response.data.get('name'), self.model_name_1)
#         self.assertEquals(len(response.data.get('topics').keys()), 2)
#         self.assertTopicExistence(response.data, 't-zero', 't-three')
#
#     def test_topic_prefer_keyphrase_all(self):
#         response = self.client.get(
#             f'{self.url}?name={self.model_name_1}&preferKeyphrase=all'
#         )
#         self.assertEquals(response.status_code, status.HTTP_200_OK)
#
#         self.assertEquals(response.data.get('name'), self.model_name_1)
#         self.assertEquals(len(response.data.get('topics').keys()), 2)
#         self.assertTopicExistence(response.data, 0, 3)
#
#     def test_topic_prefer_keyphrase_invalid(self):
#         response = self.client.get(
#             f'{self.url}?name={self.model_name_1}&preferKeyphrase=true'
#         )
#         response = self.client.get(self.url)
#         self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
#         self.assertTrue('message' in response.data)
#         self.assertEquals(len(response.data), 1)
#
#     def test_topic_prefer_keyphrase_empty(self):
#         response = self.client.get(
#             f'{self.url}?name={self.model_name_1}&preferKeyphrase='
#         )
#         response = self.client.get(self.url)
#         self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
#         self.assertTrue('message' in response.data)
#         self.assertEquals(len(response.data), 1)

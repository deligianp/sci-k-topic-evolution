from rest_framework import test, status

from topic_evolution_visualization.models import LdaModel, Topic, Term, TopicTermDistribution


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

    def assertMetaExistence(self, data, offset=None, limit=None):
        self.assertTrue('meta' in data)
        meta = data.get('meta')
        self.assertTrue('offset' in meta)
        self.assertTrue(meta.get('offset') == offset)
        self.assertTrue(meta.get('limit') == limit)

    def assertTopicExistene(self, data, *topics):
        self.assertTrue('topics' in data)
        returned_topics = set(data['topics'].keys())
        expected_topics = set(topics)
        self.assertEquals(len(returned_topics.difference(expected_topics)), 0)

    def assertNTermExistence(self, data, n_terms):
        self.assertTrue('topics' in data)
        self.assertTrue(not any((len(data['topics'][topic]) != n_terms for topic in data['topics'])))

    def test_valid_model_name(self):
        response = self.client.get(
            f'{self.url}?name={self.model_name}'
        )
        self.assertEquals(response.status_code, status.HTTP_200_OK)

        self.assertEquals(response.data.get('name'), self.model_name)
        self.assertEquals(len(response.data.get('topics').keys()), self.n_topics)
        self.assertTrue('meta' not in response.data)

    def test_invalid_model_name(self):
        response = self.client.get(
            f'{self.url}?name=invalid'
        )
        self.assertEquals(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue('message' in response.data)
        self.assertEquals(len(response.data), 1)

    def test_no_model_name(self):
        response = self.client.get(self.url)
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

    def test_valid_topic_range(self):
        offset = 1
        limit = 2
        response = self.client.get(
            f'{self.url}?name={self.model_name}&offset={offset}&limit={limit}'
        )
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(len(response.data.get('topics')), limit)

        # Assert that all topics with index from [OFFSET] up to [OFFSET+LIMIT] exclusive, have been returned
        self.assertTopicExistene(response.data, *(idx for idx in range(offset, offset + limit)))
        self.assertMetaExistence(response.data, offset, limit)

    def test_valid_topic_range_defined_only_by_offset(self):
        offset = 1
        response = self.client.get(
            f'{self.url}?name={self.model_name}&offset={offset}'
        )
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(len(response.data.get('topics')), 2)

        # Assert that all topics with index from [OFFSET] up to [OFFSET+LIMIT] exclusive, have been returned
        self.assertTopicExistene(response.data, *(idx for idx in range(offset, 3)))
        self.assertMetaExistence(response.data, offset, self.n_topics - offset)

    def test_valid_topic_range_defined_only_by_limit(self):
        limit = 2
        response = self.client.get(
            f'{self.url}?name={self.model_name}&limit={limit}'
        )
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(len(response.data.get('topics')), limit)

        # Assert that the first [LIMIT] topics have been returned
        self.assertTopicExistene(response.data, *(idx for idx in range(limit)))
        self.assertMetaExistence(response.data, 0, limit)

    def test_valid_topic_range_of_size_1(self):
        offset = 1
        limit = 1
        response = self.client.get(
            f'{self.url}?name={self.model_name}&offset={offset}&limit={limit}'
        )
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(len(response.data.get('topics')), limit)

        # Assert that the first only topic [OFFSET] has been returned, as well as 'meta' info
        self.assertTopicExistene(response.data, *(idx for idx in range(offset, offset + limit)))
        self.assertMetaExistence(response.data, offset, limit)

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

    def test_topic_range_with_valid_overextending_limit(self):
        offset = 1
        limit = 324015
        response = self.client.get(
            f'{self.url}?name={self.model_name}&offset={offset}&limit={limit}'
        )

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(len(response.data.get('topics')), self.n_topics - offset)

        # Assert that despite an excessive given [LIMIT], all topics with index greater or equal to [OFFSET] will
        # return, as well as the 'meta' information with 'limit' set to [NUMBER_OF_TOPICS - OFFSET]
        self.assertTopicExistene(response.data, *(idx for idx in range(self.n_topics)))
        self.assertMetaExistence(response.data, offset, self.n_topics - offset)

    def test_valid_nterms(self):
        offset = 1
        limit = 2
        n_terms = 2
        response = self.client.get(
            f'{self.url}?name={self.model_name}&offset={offset}&limit={limit}&nTerms={n_terms}'
        )

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(len(response.data.get('topics')), limit)

        self.assertTopicExistene(response.data, *(idx for idx in range(offset, offset + limit)))
        self.assertNTermExistence(response.data, n_terms)
        self.assertMetaExistence(response.data, offset, self.n_topics - offset)

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

    def test_overextending_nterms_number(self):
        offset = 1
        limit = 2
        n_terms = 31
        response = self.client.get(
            f'{self.url}?name={self.model_name}&offset={offset}&limit={limit}&nTerms={n_terms}'
        )

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(len(response.data.get('topics')), limit)

        self.assertTopicExistene(response.data, *(idx for idx in range(offset, offset + limit)))
        self.assertNTermExistence(response.data, self.n_terms)
        self.assertMetaExistence(response.data, offset, self.n_topics - offset)

import string

import gensim.models as g_models
from nltk import stem, tokenize

from resources import stopwords as sw
from topic_evolution import settings
from topic_evolution_visualization import queries


class PreprocessingError(ValueError):
    pass


def preprocess_text(text):
    # Remove punctuation and turn to lowercase
    table = str.maketrans('ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz',
                          string.punctuation.replace('-', ''))
    no_punc_text = text.translate(table)
    if no_punc_text.strip() != "":
        # Tokenization
        tokens = tokenize.word_tokenize(no_punc_text)
        if len(tokens) > settings.MINIMUM_WORDS_PER_TEXT:
            index = 0
            while index < len(tokens):
                if sw.is_stopword(tokens[index]):
                    del tokens[index]
                else:
                    if not str.isalpha(tokens[index]):
                        del tokens[index]
                    else:
                        lemmatizer = stem.WordNetLemmatizer()
                        stemmer = stem.snowball.SnowballStemmer('english')
                        tokens[index] = stemmer.stem(lemmatizer.lemmatize(tokens[index], pos='n'))
                        if len(tokens[index]) < 3:
                            del tokens[index]
                        else:
                            index += 1
            if len(tokens) > settings.MINIMUM_WORDS_PER_TEXT:
                return tokens
            raise PreprocessingError("Too small text after preprocessing")
        raise PreprocessingError("Too small text")
    raise PreprocessingError("Text is either empty or in an unknown encoding")


def query_lda_on_text(text_tokens, lda_model_path):
    lda_model = g_models.LdaModel.load(lda_model_path)
    text_bow_vector = lda_model.id2word.doc2bow(text_tokens)
    all_document_topics = lda_model.get_document_topics(text_bow_vector, minimum_probability=0)
    return tuple(sorted(all_document_topics, key=lambda item: item[1], reverse=True)[:settings.TOP_N_DOCUMENT_TOPICS])


def analyze_text(text, model_name=None):
    model = queries.get_model(model_name)
    abstract_tokens = preprocess_text(text)
    top_n_document_topics = query_lda_on_text(abstract_tokens, model.path)
    return top_n_document_topics

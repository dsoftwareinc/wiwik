import string
from typing import Optional

import nltk
from sklearn.feature_extraction.text import TfidfVectorizer

from similarity.apps import logger

__vectorizer: Optional[TfidfVectorizer] = None


def initialize_tfidf():
    logger.info("Initializing NLTK...")
    global __vectorizer
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt')

    stemmer = nltk.stem.porter.PorterStemmer()
    remove_punctuation_map = dict((ord(char), None) for char in string.punctuation)

    def stem_tokens(tokens):
        return [stemmer.stem(item) for item in tokens]

    def normalize(text):
        return stem_tokens(nltk.word_tokenize(text.lower().translate(remove_punctuation_map)))

    __vectorizer = TfidfVectorizer(tokenizer=normalize, stop_words='english')


initialize_tfidf()


def cosine_sim(text1, text2):
    if not __vectorizer:
        raise EnvironmentError('nltk not initialized')
    tfidf = __vectorizer.fit_transform([text1, text2])
    return ((tfidf * tfidf.T).A)[0, 1]


def calc_tfidf(docs: list[str]):
    if not __vectorizer:
        raise EnvironmentError('nltk not initialized')
    tfidf = __vectorizer.fit_transform(docs)
    return (tfidf * tfidf.T).A

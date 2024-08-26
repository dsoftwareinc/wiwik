import string
from typing import Optional

import nltk
from sklearn.feature_extraction.text import TfidfVectorizer

from similarity.apps import logger

__vectorizer: Optional[TfidfVectorizer] = None


def initialize_tfidf():
    logger.info("Initializing NLTK...")
    try:
        nltk.data.find("tokenizers/punkt")
    except LookupError:
        nltk.download("punkt_tab")

    stemmer = nltk.stem.porter.PorterStemmer()
    remove_punctuation_map = dict((ord(char), None) for char in string.punctuation)

    def stem_tokens(tokens):
        return [stemmer.stem(item) for item in tokens]

    def normalize(text):
        return stem_tokens(nltk.word_tokenize(text.lower().translate(remove_punctuation_map)))

    return TfidfVectorizer(tokenizer=normalize, stop_words="english")


def calc_tfidf_pair(text1: str, text2: str) -> float:
    global __vectorizer
    if not __vectorizer:
        __vectorizer = initialize_tfidf()
    tfidf = __vectorizer.fit_transform([text1, text2])
    return (tfidf * tfidf.T)[0,1]


def calc_tfidf_multiple_documents(docs: list[str]) -> list[list[float]]:
    global __vectorizer
    if not __vectorizer:
        __vectorizer = initialize_tfidf()
    tfidf = __vectorizer.fit_transform(docs)
    return (tfidf * tfidf.T).toarray()

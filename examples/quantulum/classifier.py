#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""quantulum classifier functions."""

import json
import os
import pickle
import re
import string

from quantulum.load import TOPDIR
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import SGDClassifier
from stemming.porter2 import stem


def clean_text(text):
    """Clean text for TFIDF."""
    punctuation_pattern = r"[" + re.escape(string.punctuation) + r"]"

    # new_text = re.sub(r'\p{P}+', ' ', text)
    new_text = re.sub(punctuation_pattern, ' ', text)

    new_text = [stem(i) for i in new_text.lower().split() if not
    re.findall(r'[0-9]', i)]

    new_text = ' '.join(new_text)

    return new_text


def train_classifier(parameters=None, ngram_range=(1, 1)):
    """Train the intent classifier."""

    path = os.path.join(TOPDIR, 'train.json')
    training_set = json.load(open(path))
    path = os.path.join(TOPDIR, 'wiki.json')
    wiki_set = json.load(open(path))

    target_names = list(set([i['unit'] for i in training_set + wiki_set]))
    train_data, train_target = [], []
    for example in training_set + wiki_set:
        train_data.append(clean_text(example['text']))
        train_target.append(target_names.index(example['unit']))

    tfidf_model = TfidfVectorizer(sublinear_tf=True,
                                  ngram_range=ngram_range,
                                  stop_words='english')

    matrix = tfidf_model.fit_transform(train_data)

    if parameters is None:
        parameters = {'loss': 'log_loss', 'penalty': 'l2', 'max_iter': 50,
                      'alpha': 0.00001, 'fit_intercept': True}

    clf = SGDClassifier(**parameters).fit(matrix, train_target)
    obj = {'tfidf_model': tfidf_model,
           'clf': clf,
           'target_names': target_names}
    path = os.path.join(TOPDIR, 'clf.pickle')
    pickle.dump(obj, open(path, 'wb'))


if __name__ == '__main__':
    train_classifier()

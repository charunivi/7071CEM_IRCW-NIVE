#
# Libraries
#
import re
from collections import defaultdict, Counter

import nltk
import pandas as pd
from flask import Flask, request, flash, render_template
from flask_paginate import Pagination, get_page_args
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from flask import session

# import indexer

SPLIT_RE = re.compile(r'[^a-zA-Z0-9]')


import nltk
nltk.download('stopwords')
nltk.download('wordnet')
nltk.download('omw-1.4')

def tokenize(text):
    yield from SPLIT_RE.split(text)


def text_only(tokens):
    for t in tokens:
        if t.isalnum():
            yield t


def lowercase(tokens):
    for t in tokens:
        yield t.lower()


def get_stopwords():
    stop_words = set(stopwords.words('english'))
    return stop_words


def remove_stop_words(tokens):
    stop_words = get_stopwords()
    filtered_words = [token for token in tokens if token not in stop_words and len(token) > 2]
    return filtered_words


def lemmatized_words(tokens):
    lemmatizer = WordNetLemmatizer()
    lemmatized_words = [lemmatizer.lemmatize(token) for token in tokens]
    return lemmatized_words


def stemming(tokens):
    for t in tokens:
        if t.endswith('ly'):
            t = t[:-2]
        yield t


def analyzetext(text):
    if text is not None:
        tokens = tokenize(text)
        for token_filter in (remove_stop_words, text_only, lowercase, stemming, lemmatized_words, remove_stop_words):
            tokens = token_filter(tokens)
        yield from tokens


def index_docs(docs, *fields):
    index = defaultdict(lambda: defaultdict(Counter))
    for id, doc in enumerate(docs):
        for field in fields:
            for token in analyzetext(doc[field]):
                index[field][token][id] += 1
    return index


def intersection(*args):
    if not args:
        return Counter()
    out = args[0].copy()
    for c in args[1:]:
        for doc_id in list(out):
            if doc_id not in c:
                del out[doc_id]
            else:
                out[doc_id] += c[doc_id]
    return out


def difference(*args):
    if not args:
        return Counter()
    out = args[0].copy()
    for c in args[1:]:
        out.update(c)
    return out


def search_in_fields(index, query, fields):
    for t in analyzetext(query):
        yield difference(*(index[f][t] for f in fields))


def search(index, query, operator, fields=None):
    if operator == 'OR':
        combine = difference
    elif operator == 'AND':
        combine = intersection
    return combine(*(search_in_fields(index, query, fields or index.keys())))


def query(index, data, query, fields=None):
    interids = search(index, query, 'AND', fields)
    diffids = search(index, query, 'OR', fields)
    search_results = []
    docid = []
    for interdoc_id, interscore in interids.most_common():
        temp = createjsondata(data, interdoc_id)
        docid.append(interdoc_id)
        search_results.append(temp)
    for diffdoc_id, diffscore in diffids.most_common():
        if diffdoc_id not in docid:
            temp = createjsondata(data, diffdoc_id)
            search_results.append(temp)
    return search_results[:1000]


def createjsondata(data, doc_id):
    return {
        'Title': data[doc_id]['Title'],
        # 'Paper_Link': data[doc_id]['Paper_Link'],
        'Pub_Year': data[doc_id]['Pub_Year'],
        'Pub_auth': data[doc_id]['Pub_auth'],
        'Abstract': data[doc_id]['Abstract'],
        'Tags': data[doc_id]['Tags'],
        'Department': data[doc_id]['Department'],
        'Access_Doc': data[doc_id]['Access_Doc']
    }


app = Flask(__name__)

#
# Routes
#
# getting the data from  and passing
dataframe = pd.read_json("CGL_Research_Paper.json")
dataframe = dataframe.drop_duplicates(subset=['Title', 'Pub_auth', 'Tags', 'Department', 'Abstract', 'Access_Doc'])
DATA = dataframe.to_dict('records')
index = index_docs(DATA, 'Title', 'Pub_auth', 'Tags', 'Department', 'Abstract', 'Access_Doc')


@app.route('/')
def home():
    if 'search' in request.args:
        searchword = request.args.get('search')
        search_results = query(index, DATA, searchword)

        for entry in search_results:
            flash(entry, 'success')
    return render_template('search.html')


@app.route('/search_results')
def search_results():
    session.clear()
    if 'search' in request.args:
        searchword = request.args.get('search')
        search_results = query(index, DATA, searchword)
        for entry in search_results:
            flash(entry, 'success')

        # automatic pagination handling
        total = len(search_results)
        page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page')
        pagination = Pagination(page=page, per_page=per_page, total=total, css_framework='bootstrap5')

        return render_template('search_results.html',
                               search_results=search_results[offset: offset + per_page],
                               search_item=searchword,
                               page=page,
                               per_page=per_page,
                               pagination=pagination,
                               len=len)


if __name__ == '__main__':
    app.secret_key = 'secret123'
    app.run(debug=True, threaded=True)

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


# import indexer

# SPLIT_RE = re.compile(r'[^a-zA-Z0-9]')
# import nltk
# nltk.download('stopwords')
# nltk.download('wordnet')
# nltk.download('omw-1.4')

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
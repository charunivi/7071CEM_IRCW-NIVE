import pandas as pd
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.model_selection import GridSearchCV
from sklearn.svm import SVC
from sklearn.linear_model import SGDClassifier
from sklearn.metrics import accuracy_score
import json
from gensim.utils import simple_preprocess

data = pd.read_csv('BBC_News.csv')
dataCopy = data
data.head()
data['Category'].value_counts()
data.Text = data.Text.apply(simple_preprocess, min_len=3)
data.Text.head()
stop_words = set(stopwords.words('english'))


def stemmingandstop(lis):
    lemmatizer = WordNetLemmatizer()
    filtered_lis = [lemmatizer.lemmatize(w) for w in lis if not w in stop_words and len(w) > 2]
    return filtered_lis


data.Text = data.Text.apply(stemmingandstop)
data.Text.head()
type(data.Text)
data.Text = data.Text.apply(' '.join)
data.head()


X = data.Text
y = data.Category


X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

svm_clftfidf = Pipeline([
    ('vect', CountVectorizer()),
    ('tfidf', TfidfTransformer()),
    ('clf', MultinomialNB()),
])

svm_clftfidf.fit(X_train, y_train)
tfsvmpred = svm_clftfidf.predict(X_test)
print(accuracy_score(y_test, tfsvmpred))

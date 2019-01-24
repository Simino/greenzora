from server import server_app, utils, db
from server.models import Paper
import csv
import pandas as pd
import sklearn

# initialize the vectorizer
vectorizer = sklearn.CountVectorizer()

# initialize the classifier
classifier = sklearn.MultinomialNB()


# TODO: Handle error cases (multiple db entries found, no entries found, etc.)
def import_legacy_annotations():
    file_path = server_app.config['LEGACY_ANNOTATIONS_PATH']
    with open(file_path, 'rt') as file:
        reader = csv.reader(file)
        annotation_list = list(reader)
    for eprint_id, label in annotation_list:
        paper = Paper.query.filter(Paper.uid.contains(eprint_id).first())
        if paper:
            paper.set_annotation(label)
    if utils.is_debug():
        print('Legacy annotations imported')


def load_data(annotated):



def train_classifier():
    # Get papers from database if they are annotated
    data_set = pd.read_sql_query(db.session.query(Paper).filter(Paper.annotated is True).statement, db.session.bind)

    # Create a merged field containing title and abstract, since we will only use this information for the training.
    merged_column_name = 'title_abstract'
    data_set[merged_column_name] = data_set["title"] + " | " + data_set["abstract"]

    training_data = data_set.iloc[:, merged_column_name].values
    labels = data_set.label

    # Learn data vocabulary, then use it to create a document-term matrix
    training_data_dtm = vectorizer.fit_transform(training_data)

    # Train the model using X_train_dtm
    classifier.fit(training_data_dtm, labels)


def classify_papers():
    # Get papers from database that are not annotated
    data_set = pd.read_sql_query(db.session.query(Paper).filter(Paper.annotated is False).statement, db.session.bind)

    # Set the uid as index so we still can assign the results to the right papers
    data_set = data_set.index('uid')

    # Create a merged field containing title and abstract and extract it.
    # We do this, since we will only use this information for the training.
    merged_column_name = 'title_abstract'
    data_set[merged_column_name] = data_set["title"] + " | " + data_set["abstract"]
    training_data = data_set.loc[:, merged_column_name].values

    # Transform data (using fitted vocabulary of vectorizer) into a document-term matrix
    training_data_dtm = vectorizer.transform(training_data)

    # Predict the labels
    label_pred = classifier.predict(training_data_dtm)

    data_set['label'] = label_pred

    #TODO: Might be slow as fuck
    # Write the results into the database
    for uid, row in data_set.iterrows():
        paper = Paper.query.get(uid)
        paper.set_annotation(bool(row['label']))

def create_new_model():
    # Reset the vectorizer and the classifier
    global vectorizer, classifier
    vectorizer = sklearn.CountVectorizer()
    classifier = sklearn.MultinomialNB()

    train_classifier()
    classify_papers()

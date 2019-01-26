from server import server_app, utils, db
from server.models import Paper
import json
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB

# initialize the vectorizer
vectorizer = CountVectorizer()

# initialize the classifier
classifier = MultinomialNB()


# TODO: Handle error cases (multiple db entries found, no entries found, etc.)
def import_legacy_annotations():
    file_path = server_app.config['LEGACY_ANNOTATIONS_PATH']
    with open(file_path, 'rt') as file:
        paper_dict_list = json.load(file)
    for paper_dict in paper_dict_list:

        # Check if the paper already exists in the database. If it does, we only want to set the sustainable and
        # annotated values (since we can assume that the other existing values are more recent). Otherwise we
        # create a new entry in the database.
        paper = db.session.query(Paper).filter_by(uid=paper_dict['uid']).first()
        if paper:
            paper.sustainable = paper_dict['sustainable']
            paper.annotated = paper_dict['annotated']
        else:
            paper = Paper(**paper_dict)
            db.session.add(paper)
    db.session.commit()
    if utils.is_debug():
        print('Legacy annotations imported')


def train_classifier():
    # Get papers from database if they are annotated
    data_set = pd.read_sql_query(db.session.query(Paper).filter(Paper.annotated == True).statement, db.session.bind)

    # Create a merged field containing title and description (abstract), since we will only use this information for the training.
    merged_column_name = 'title_abstract'
    data_set[merged_column_name] = data_set["title"] + " | " + data_set["description"]

    training_data = data_set.loc[:, merged_column_name].values
    labels = data_set.sustainable

    # TODO: Division by zero warning
    # Learn data vocabulary, then use it to create a document-term matrix
    training_data_dtm = vectorizer.fit_transform(training_data)

    # Train the model using X_train_dtm
    classifier.fit(training_data_dtm, labels)

def classify_papers():
    # Get papers from database that are not annotated and that include title and abstract.
    data_set = pd.read_sql_query(db.session.query(Paper).filter(Paper.annotated == False, Paper.title != None, Paper.description != None).statement, db.session.bind)

    # Create a merged field containing title and description (abstract) and extract it.
    # We do this, since we will only use this information for the training.
    merged_column_name = 'title_abstract'
    data_set[merged_column_name] = data_set["title"] + " | " + data_set["description"]
    data = data_set.loc[:, merged_column_name].values

    # Transform data (using fitted vocabulary of vectorizer) into a document-term matrix
    data_dtm = vectorizer.transform(data)

    # Predict the labels
    data_set['label'] = classifier.predict(data_dtm)

    count = 0
    #TODO: Might be slow as fuck
    # Write the results into the database
    for index, row in data_set.iterrows():
        paper = db.session.query(Paper).get(row['uid'])
        paper.sustainable = bool(row['label'])
        if utils.is_debug() and row['label']:
            print(row['uid'] + ':' + row[merged_column_name] + ' - sustainable: ' + str(bool(row['label'])))
        if utils.is_debug():
            print(count)
            count += 1
    db.session.commit()


def create_new_model():
    # Reset the vectorizer and the classifier
    global vectorizer, classifier
    vectorizer = CountVectorizer()
    classifier = MultinomialNB()

    train_classifier()
    classify_papers()


def initialize_ml_tool():
    import_legacy_annotations()
    create_new_model()

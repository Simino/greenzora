import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB


class MLTool:

    def __init__(self):
        # initialize the vectorizer
        self.vectorizer = CountVectorizer()

        # initialize the classifier
        self.classifier = MultinomialNB()

    # This method creates the vocabulary and trains the classifier based on the trainings data and labels provided.
    def train_classifier(self, training_data: pd.Series, labels: pd.Series):

        # Learn data vocabulary, then use it to create a document-term matrix
        training_data_dtm = self.vectorizer.fit_transform(training_data)

        # Train the model using X_train_dtm
        self.classifier.fit(training_data_dtm, labels)

    def classify(self, data: pd.Series):

        # Transform data (using fitted vocabulary of vectorizer) into a document-term matrix
        data_dtm = self.vectorizer.transform(data)

        # Predict the label and store it
        return self.classifier.predict(data_dtm)

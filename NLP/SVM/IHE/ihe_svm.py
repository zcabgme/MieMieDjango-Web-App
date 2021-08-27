import time, sys
import datetime
import pandas as pd
import numpy as np
import json

from NLP.SVM.svm import Svm
from NLP.PREPROCESSING.preprocessor import Preprocessor

class IheSvm(Svm):
    """
        Concrete class to classify SDGs for modules and publications using the Svm model.
    """

    def __init__(self):
        super().__init__()

    def make_text_predictions(self, text, preprocessor):
        """
            Predicts probabilities of SDGs given any random text input.
        """
        text = preprocessor.preprocess(text)
        y_pred = self.sgd_pipeline.predict_proba([text])
        return y_pred

    def run(self) -> None:
        """
            Trains the SVM model for clasifying SDGs using stochastic gradient descent.
        """
        ts = time.time()
        startTime = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

        svm_dataset = "NLP/SVM/IHE/SVM_dataset_ihe.csv"
        
        tags = ['IHE {}'.format(i) for i in range(1, 10)]  # IHE tags.

        # SDG results files.
        model = "NLP/SVM/IHE/model.pkl"

        self.load_dataset(svm_dataset)
        self.load_tags(tags)
        print("Loaded dataset: size =", len(self.dataset))

        print("Training...")
        X_train, X_test, y_train, y_test = self.train()


        print("Saving results...")
        self.serialize(model)

        print("Done.")
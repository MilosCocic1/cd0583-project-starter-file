"""
Module that trains a logistic regression model that predicts attrition risk
`exicted`from the three numeric predictors in finaldata.csv, and
saves the trained model to output_model_path as trainedmodel.pkl.

Author: Miloš Ćoćić
Date: 9.8.2026.
"""
import json
import os
import pickle
import pandas as pd
from sklearn.linear_model import LogisticRegression

with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

output_folder_path = config['output_folder_path']
output_model_path = config['output_model_path']

PREDICTOR_COLUMNS = [
    'lastmonth_activity',
    'lastyear_activity',
    'number_of_employees']
TARGET_COLUMN = 'exited'


def train_model():
    """
    Train a logistic regression model on finaldata.csv and save it as
    trainedmodel.pkl in output_model_path.
    """
    data = pd.read_csv(os.path.join(output_folder_path, 'finaldata.csv'))

    X = data[PREDICTOR_COLUMNS]
    y = data[TARGET_COLUMN]

    model = LogisticRegression(
        solver='liblinear',
        max_iter=100,
        random_state=0,
    )

    model.fit(X, y)

    os.makedirs(output_model_path, exist_ok=True)
    model_path = os.path.join(output_model_path, 'trainedmodel.pkl')
    with open(model_path, 'wb') as model_file:
        pickle.dump(model, model_file)

    return model_path


if __name__ == '__main__':
    train_model()

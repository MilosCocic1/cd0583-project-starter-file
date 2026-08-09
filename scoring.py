"""
Module that reads the test dataset (test_data_path) and the trained model
(output_model_path), computes the F1 score, and writes it to
latestscore.txt in output_model_path.

Author: Miloš Ćoćić
Date: 9.8.2026.
"""
import json
import os
import pickle
from datetime import datetime
import pandas as pd
from sklearn.metrics import f1_score
import dbsetup

with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

output_model_path = config['output_model_path']
test_data_path = config['test_data_path']

PREDICTOR_COLUMNS = [
    'lastmonth_activity',
    'lastyear_activity',
    'number_of_employees']
TARGET_COLUMN = 'exited'


def score_model(model_dir=None, test_dir=None):
    """
    Score the trained model against the test dataset and write the F1
    score to latestscore.txt. Returns the F1 score as a float.

     Input:
        model_dir: Directory containing trainedmodel.pkl, and where
            latestscore.txt is written. Defaults to output_model_path.
        test_dir: Directory of one or more .csv files to score against. Defaults to
            test_data_path.
    Output:
        The F1 score: float.
    """
    model_dir = model_dir or output_model_path
    test_dir = test_dir or test_data_path

    test_files = [file_name for file_name in os.listdir(
        test_dir) if file_name.endswith('.csv')]
    test_data = pd.concat(
        (pd.read_csv(
            os.path.join(
                test_dir,
                file_name)) for file_name in test_files),
        ignore_index=True,
    )

    with open(os.path.join(model_dir, 'trainedmodel.pkl'), 'rb') as model_file:
        model = pickle.load(model_file)

    X = test_data[PREDICTOR_COLUMNS]
    y = test_data[TARGET_COLUMN]
    predictions = model.predict(X)

    f1 = f1_score(y, predictions)

    os.makedirs(model_dir, exist_ok=True)
    with open(
        os.path.join(model_dir, 'latestscore.txt'), 'w', encoding='utf-8'
    ) as score_file:
        score_file.write(str(f1))

    try:
        dbsetup.log_model_score(float(f1), test_dir, datetime.now())
    except Exception as exc:
        print(
            f"[scoring] Skipping database logging (MySQL unavailable?): {exc}")

    return f1


if __name__ == '__main__':
    print(score_model())

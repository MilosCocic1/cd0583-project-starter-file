"""
Module that provides four diagnostic capabilities, used both by app.py's API
endpoints and by fullprocess.py:

  - model_predictions(data)   -> predictions from the deployed model
  - dataframe_summary()       -> mean/median/std for each numeric column
  - missing_data()            -> percent of NA values per column
  - execution_time()          -> timing (seconds) of ingestion + training
  - outdated_packages_list()  -> installed vs. latest version per dependency

Author: Miloš Ćoćić
Date: 12.8.2026.
"""
import json
import os
import pickle
import subprocess
import sys
import timeit
from datetime import datetime
from importlib import metadata
import pandas as pd
import dbsetup

with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

output_folder_path = config['output_folder_path']
prod_deployment_path = config['prod_deployment_path']

PREDICTOR_COLUMNS = [
    'lastmonth_activity',
    'lastyear_activity',
    'number_of_employees']


def model_predictions(data):
    """
    Return a list of predictions made by the deployed model for the
    rows of the given DataFrame.
    """
    with open(os.path.join(prod_deployment_path, 'trainedmodel.pkl'), 'rb') as model_file:
        model = pickle.load(model_file)

    predictions = model.predict(data[PREDICTOR_COLUMNS])
    return predictions.tolist()


def dataframe_summary():
    """
    Return mean/median/std for every numeric column of finaldata.csv,
    as a list of dicts, and log them to the database.
    """
    data = pd.read_csv(os.path.join(output_folder_path, 'finaldata.csv'))
    numeric_data = data.select_dtypes(include='number')

    summary = []
    for column in numeric_data.columns:
        summary.append({
            'column': column,
            'mean': float(numeric_data[column].mean()),
            'median': float(numeric_data[column].median()),
            'std': float(numeric_data[column].std()),
        })

    try:
        dbsetup.log_summary_stats(summary, datetime.now())
    except Exception as exc:  # pylint: disable=broad-exception-caught
        print(
            f"[diagnostics] Skipping database logging (MySQL unavailable?): {exc}")

    return summary


def missing_data():
    """
    Return the percentage of NA values in each column of
    finaldata.csv, and log them to the database.
    """
    data = pd.read_csv(os.path.join(output_folder_path, 'finaldata.csv'))

    na_percent = (data.isna().sum() / len(data) * 100).round(2)
    result = {column: float(value) for column, value in na_percent.items()}

    try:
        dbsetup.log_missing_data(result, datetime.now())
    except Exception as exc:  # pylint: disable=broad-exception-caught
        print(
            f"[diagnostics] Skipping database logging (MySQL unavailable?): {exc}")

    return list(result.values())


def execution_time():
    """
    Time how long ingestion.py and training.py each take to run (in
    seconds), and log the timings to the database.
    """
    timings = []
    for script in ('ingestion.py', 'training.py'):
        start_time = timeit.default_timer()
        subprocess.run([sys.executable, script], check=True)
        timings.append(timeit.default_timer() - start_time)

    try:
        dbsetup.log_timing(timings[0], timings[1], datetime.now())
    except Exception as exc:  # pylint: disable=broad-exception-caught
        print(
            f"[diagnostics] Skipping database logging (MySQL unavailable?): {exc}")

    return timings


def outdated_packages_list():
    """
    Return a DataFrame with one row per module in requirements.txt,
    showing its installed version and the latest version available on
    PyPI, using `pip list --outdated` as the source of truth.
    """
    with open('requirements.txt', 'r', encoding='utf-8') as requirements_file:
        requirement_lines = [
            line.strip() for line in requirements_file if line.strip()
        ]

    module_names = [line.split('==')[0] for line in requirement_lines]

    outdated_raw = subprocess.check_output(
        [sys.executable, '-m', 'pip', 'list', '--outdated', '--format=json']
    )
    outdated_by_name = {
        pkg['name'].lower(): pkg['latest_version']
        for pkg in json.loads(outdated_raw)
    }

    rows = []
    for name in module_names:
        try:
            installed_version = metadata.version(name)
        except metadata.PackageNotFoundError:
            installed_version = 'not installed'

        latest_version = outdated_by_name.get(name.lower(), installed_version)

        rows.append({
            'module': name,
            'installed_version': installed_version,
            'latest_version': latest_version,
        })

    return pd.DataFrame(rows)


if __name__ == '__main__':
    input_data = pd.read_csv(
        os.path.join(
            config['test_data_path'],
            'testdata.csv'))
    print(model_predictions(input_data))
    print(dataframe_summary())
    print(missing_data())
    print(execution_time())
    print(outdated_packages_list())

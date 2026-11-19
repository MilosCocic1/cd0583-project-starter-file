"""
Module exposes four endpoints so colleagues can pull ML diagnostics and results
without touching the scripts directly. Every endpoint returns HTTP 200.

  POST /prediction?filepath=<csv>   -> predictions from the deployed model
  GET  /scoring                     -> F1 score of the current model
  GET  /summarystats                -> summary statistics of ingested data
  GET  /diagnostics                 -> timing, missing data, dependencies

The read-only JSON API for the monitoring dashboard lives in api.py and
is registered under /api.

These endpoints have no authentication, and /scoring and /diagnostics
write files and retrain the model, so the server listens on 127.0.0.1
by default. Set FLASK_HOST=0.0.0.0 to expose it (e.g. inside a
container), and only on a trusted network. /prediction only reads .csv
files inside the project's data folders.

Author: Miloš Ćoćić
Date: 12.8.2026.
"""
import json
import os
import secrets
from flask import Flask, jsonify, request
import pandas as pd
import diagnostics
import scoring
from api import api

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY') or secrets.token_hex(32)
app.register_blueprint(api)

with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

# The only folders /prediction may read from.
PREDICTION_DATA_DIRS = [
    os.path.realpath(config[key])
    for key in ('test_data_path', 'output_folder_path', 'input_folder_path')
]


def resolve_prediction_file(file_path):
    """
    Return the absolute path of file_path if it is an existing .csv file
    inside one of PREDICTION_DATA_DIRS, otherwise None. Resolving the
    real path first stops '../' tricks and symlinks from escaping those
    folders, and URLs never resolve to a file inside them.
    """
    real_path = os.path.realpath(file_path)
    if not real_path.lower().endswith('.csv') or not os.path.isfile(real_path):
        return None
    for data_dir in PREDICTION_DATA_DIRS:
        try:
            if os.path.commonpath([real_path, data_dir]) == data_dir:
                return real_path
        except ValueError:  # different drive on Windows
            continue
    return None


@app.route('/prediction', methods=['POST'])
def predict():
    """
    Return predictions from the deployed model for the dataset at
    the given file path.
    """
    file_path = request.args.get('filepath') or (
        request.get_json(silent=True) or {}).get('filepath')

    if not file_path:
        return jsonify({'error': 'filepath is required'}), 200

    safe_path = resolve_prediction_file(file_path)
    if safe_path is None:
        return jsonify({
            'error': 'filepath must be an existing .csv file in the '
                     'test, ingested or source data folder'
        }), 200

    data = pd.read_csv(safe_path)
    predictions = diagnostics.model_predictions(data)
    return jsonify({'predictions': predictions}), 200


@app.route('/scoring', methods=['GET'])
def scoring_endpoint():
    """Run scoring.py and return the F1 score."""
    f1 = scoring.score_model()
    return jsonify({'f1_score': f1}), 200


@app.route('/summarystats', methods=['GET'])
def summarystats_endpoint():
    """
    Return mean/median/std for every numeric column of the ingested
    data.
    """
    summary_statistics = diagnostics.dataframe_summary()
    return jsonify({'summary_statistics': summary_statistics}), 200


@app.route('/diagnostics', methods=['GET'])
def diagnostics_endpoint():
    """Return timing, missing-data, and dependency diagnostics."""
    execution_times = diagnostics.execution_time()
    missing_percentages = diagnostics.missing_data()
    dependency_table = diagnostics.outdated_packages_list().to_dict(orient='records')

    return jsonify({
        'execution_time': execution_times,
        'missing_data_percent': missing_percentages,
        'outdated_packages': dependency_table,
    }), 200


if __name__ == '__main__':
    app.run(
        host=os.environ.get('FLASK_HOST', '127.0.0.1'),
        port=8000,
        debug=os.environ.get('FLASK_DEBUG') == '1',
        threaded=True,
    )

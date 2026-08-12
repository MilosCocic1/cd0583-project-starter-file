"""
Module exposes four endpoints so colleagues can pull ML diagnostics and results
without touching the scripts directly. Every endpoint returns HTTP 200.

  POST /prediction?filepath=<csv>   -> predictions from the deployed model
  GET  /scoring                     -> F1 score of the current model
  GET  /summarystats                -> summary statistics of ingested data
  GET  /diagnostics                 -> timing, missing data, dependencies

Author: Miloš Ćoćić
Date: 12.8.2026.
"""
import json
from flask import Flask, jsonify, request
import pandas as pd
import diagnostics
import scoring

app = Flask(__name__)
app.secret_key = '1652d576-484a-49fd-913a-6879acfa6ba4'

with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)


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

    data = pd.read_csv(file_path)
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
    app.run(host='0.0.0.0', port=8000, debug=True, threaded=True)

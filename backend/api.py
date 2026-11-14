"""
Module with the JSON API that the monitoring dashboard reads. It is
registered in app.py under the /api prefix:

  GET /api/health                          -> API, database and model status
  GET /api/runs?limit=20&include_idle=0    -> most recent pipeline runs
  GET /api/metrics?limit=100               -> F1/AUC history from model_scores
  GET /api/drift                           -> deployed model and last drift check

Unlike app.py's endpoints, these only read what the pipeline has already
recorded; they never retrain, rescore or write anything.

Author: Miloš Ćoćić
Date: 14.11.2026.
"""
import os
from datetime import datetime
from flask import Blueprint, jsonify, request
from mysql.connector import Error as MySQLError
import dbsetup
import deployment

api = Blueprint('api', __name__, url_prefix='/api')

BOOLEAN_COLUMNS = ('drift_detected', 'retrained')


def _serialize(row):
    """
    Make a database row JSON friendly: datetimes become ISO strings and
    MySQL's 0/1 booleans become true/false.
    """
    if row is None:
        return None
    result = {}
    for key, value in row.items():
        if isinstance(value, datetime):
            value = value.isoformat()
        elif key in BOOLEAN_COLUMNS and value is not None:
            value = bool(value)
        result[key] = value
    return result


def _int_arg(name, default, maximum):
    """Read a positive integer query parameter, clamped to [1, maximum]."""
    value = request.args.get(name, default, type=int)
    return max(1, min(value, maximum))


def _deployed_score():
    """Return the score the deployed model was deployed with, or None."""
    score_path = os.path.join(deployment.prod_deployment_path, 'latestscore.txt')
    if not os.path.exists(score_path):
        return None
    with open(score_path, 'r', encoding='utf-8') as score_file:
        return float(score_file.read().strip())


@api.errorhandler(MySQLError)
def database_unavailable(exc):
    """Return 503 instead of a stack trace when MySQL can't be reached."""
    return jsonify({'error': 'database unavailable', 'detail': str(exc)}), 503


@api.route('/health', methods=['GET'])
def health():
    """Report whether the API is up, MySQL is reachable, and which model
    version is deployed. Always returns 200 so it works as a liveness
    check even when the database is down."""
    try:
        dbsetup.get_connection().close()
        database = 'ok'
    except MySQLError:
        database = 'unavailable'

    return jsonify({
        'status': 'ok',
        'database': database,
        'model_version': deployment.get_model_version(),
    }), 200


@api.route('/runs', methods=['GET'])
def runs():
    """Return the most recent pipeline runs, newest first."""
    limit = _int_arg('limit', 20, 200)
    include_idle = request.args.get('include_idle', '0').lower() in ('1', 'true')
    rows = dbsetup.get_pipeline_runs(limit=limit, include_idle=include_idle)
    return jsonify({'runs': [_serialize(row) for row in rows]}), 200


@api.route('/metrics', methods=['GET'])
def metrics():
    """Return the F1/AUC score history, oldest first."""
    limit = _int_arg('limit', 100, 500)
    rows = dbsetup.get_model_scores(limit=limit)
    return jsonify({'metrics': [_serialize(row) for row in rows]}), 200


@api.route('/drift', methods=['GET'])
def drift():
    """Return the deployed model's version and score, the last run that
    actually checked for drift, and the last run of any kind (so the
    dashboard can show whether the scheduler is still running)."""
    last_check = dbsetup.get_latest_pipeline_run(statuses=('no_drift', 'retrained'))
    last_run = dbsetup.get_latest_pipeline_run()

    return jsonify({
        'model_version': deployment.get_model_version(),
        'deployed_score': _deployed_score(),
        'last_check': _serialize(last_check),
        'last_run': _serialize(last_run),
    }), 200

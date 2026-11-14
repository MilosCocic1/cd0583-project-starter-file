"""
Tests for the dashboard JSON API (api.py). The database functions are
replaced with fakes, so these run without MySQL.
"""
from datetime import datetime

from mysql.connector import Error as MySQLError

import dbsetup
import deployment

RETRAINED_RUN = {
    'id': 7,
    'started_at': datetime(2026, 11, 14, 10, 0, 0),
    'finished_at': datetime(2026, 11, 14, 10, 0, 5),
    'status': 'retrained',
    'new_files': 'dataset4.csv',
    'deployed_score': 0.9,
    'new_data_score': 0.545,
    'drift_detected': 1,
    'retrained': 1,
    'new_model_score': 0.333,
    'model_version': 2,
    'error_message': None,
}


def _raise_db_error(*args, **kwargs):
    raise MySQLError('connection refused')


def test_health_reports_database_ok(client, monkeypatch):
    class FakeConnection:
        def close(self):
            pass

    monkeypatch.setattr(dbsetup, 'get_connection', FakeConnection)
    monkeypatch.setattr(deployment, 'get_model_version', lambda: 3)

    response = client.get('/api/health')

    assert response.status_code == 200
    assert response.get_json() == {
        'status': 'ok', 'database': 'ok', 'model_version': 3}


def test_health_stays_up_when_database_is_down(client, monkeypatch):
    monkeypatch.setattr(dbsetup, 'get_connection', _raise_db_error)

    response = client.get('/api/health')

    assert response.status_code == 200
    assert response.get_json()['database'] == 'unavailable'


def test_runs_serializes_dates_and_booleans(client, monkeypatch):
    calls = {}

    def fake_get_pipeline_runs(limit, include_idle):
        calls.update(limit=limit, include_idle=include_idle)
        return [RETRAINED_RUN]

    monkeypatch.setattr(dbsetup, 'get_pipeline_runs', fake_get_pipeline_runs)

    response = client.get('/api/runs')
    run = response.get_json()['runs'][0]

    assert response.status_code == 200
    assert calls == {'limit': 20, 'include_idle': False}
    assert run['started_at'] == '2026-11-14T10:00:00'
    assert run['drift_detected'] is True
    assert run['retrained'] is True
    assert run['model_version'] == 2


def test_runs_query_parameters(client, monkeypatch):
    calls = {}

    def fake_get_pipeline_runs(limit, include_idle):
        calls.update(limit=limit, include_idle=include_idle)
        return []

    monkeypatch.setattr(dbsetup, 'get_pipeline_runs', fake_get_pipeline_runs)

    client.get('/api/runs?limit=100000&include_idle=1')
    assert calls == {'limit': 200, 'include_idle': True}

    client.get('/api/runs?limit=0')
    assert calls['limit'] == 1


def test_metrics_returns_score_history(client, monkeypatch):
    rows = [
        {'id': 1, 'f1_score': 0.5, 'auc_score': None,
         'dataset_source': 'testdata', 'recorded_at': datetime(2026, 11, 1)},
        {'id': 2, 'f1_score': 0.6, 'auc_score': 0.7,
         'dataset_source': 'ingesteddata', 'recorded_at': datetime(2026, 11, 2)},
    ]
    monkeypatch.setattr(dbsetup, 'get_model_scores', lambda limit: rows)

    response = client.get('/api/metrics')
    metrics = response.get_json()['metrics']

    assert response.status_code == 200
    assert [m['f1_score'] for m in metrics] == [0.5, 0.6]
    assert metrics[0]['auc_score'] is None
    assert metrics[1]['recorded_at'] == '2026-11-02T00:00:00'


def test_drift_returns_last_check_and_last_run(client, monkeypatch):
    idle_run = dict(RETRAINED_RUN, id=8, status='no_new_data',
                    drift_detected=None, retrained=0)

    def fake_get_latest_pipeline_run(statuses=None):
        return RETRAINED_RUN if statuses else idle_run

    monkeypatch.setattr(
        dbsetup, 'get_latest_pipeline_run', fake_get_latest_pipeline_run)
    monkeypatch.setattr(deployment, 'get_model_version', lambda: 2)

    body = client.get('/api/drift').get_json()

    assert body['model_version'] == 2
    assert isinstance(body['deployed_score'], float)
    assert body['last_check']['status'] == 'retrained'
    assert body['last_run']['status'] == 'no_new_data'
    assert body['last_run']['drift_detected'] is None


def test_database_error_returns_503(client, monkeypatch):
    monkeypatch.setattr(dbsetup, 'get_pipeline_runs', _raise_db_error)

    response = client.get('/api/runs')

    assert response.status_code == 503
    assert response.get_json()['error'] == 'database unavailable'

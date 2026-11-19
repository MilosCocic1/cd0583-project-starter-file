"""
Tests for /prediction's filepath check: only existing .csv files inside
the project's data folders may be read.
"""
import os

import pytest

import diagnostics


@pytest.fixture(autouse=True)
def fake_predictions(monkeypatch):
    """Skip loading the deployed model; return one prediction per row."""
    monkeypatch.setattr(diagnostics, 'model_predictions',
                        lambda data: [0] * len(data))


def test_prediction_reads_csv_in_test_data_folder(client):
    response = client.post('/prediction?filepath=testdata/testdata.csv')

    body = response.get_json()
    assert 'error' not in body
    assert len(body['predictions']) > 0


@pytest.mark.parametrize('file_path', [
    '../README.md',                                  # outside data folders
    'testdata/../config.json',                       # '../' escape
    os.path.abspath('requirements.txt'),             # absolute path outside
    'http://169.254.169.254/latest/meta-data.csv',   # URL (SSRF)
    'testdata/missing.csv',                          # does not exist
    'ingesteddata/ingestedfiles.txt',                # not a .csv
])
def test_prediction_rejects_paths_outside_data_folders(client, file_path):
    response = client.post('/prediction', query_string={'filepath': file_path})

    body = response.get_json()
    assert 'predictions' not in body
    assert 'filepath must be' in body['error']


def test_prediction_requires_filepath(client):
    response = client.post('/prediction')

    assert response.get_json() == {'error': 'filepath is required'}

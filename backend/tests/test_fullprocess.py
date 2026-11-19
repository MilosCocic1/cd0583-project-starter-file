"""
Tests for the deployment gate in fullprocess.run_pipeline: after drift is
detected and the model is retrained, the new model is deployed only if it
scores at least as well as the deployed one. Every step that touches
files, the model or the database is replaced with a stub.
"""
import pytest

import fullprocess


@pytest.fixture
def pipeline(monkeypatch):
    """Stub the pipeline steps and record which ones ran."""
    calls = []

    monkeypatch.setattr(fullprocess, 'get_new_files', lambda: ['dataset3.csv'])
    monkeypatch.setattr(fullprocess.ingestion, 'merge_multiple_dataframe',
                        lambda: calls.append('ingest'))
    monkeypatch.setattr(fullprocess, 'check_for_model_drift',
                        lambda: (True, 0.60, 0.40))
    monkeypatch.setattr(fullprocess.training, 'train_model',
                        lambda: calls.append('train'))
    monkeypatch.setattr(fullprocess.deployment, 'deploy_model',
                        lambda: calls.append('deploy'))
    monkeypatch.setattr(fullprocess.deployment, 'get_model_version', lambda: 2)
    monkeypatch.setattr(fullprocess, 'mark_new_files_as_seen',
                        lambda: calls.append('mark_seen'))
    monkeypatch.setattr(fullprocess.reporting, 'plot_confusion_matrix',
                        lambda **kwargs: calls.append('report'))
    monkeypatch.setattr(fullprocess.apicalls, 'call_api_endpoints',
                        lambda: calls.append('apicalls'))
    monkeypatch.setattr(fullprocess.apicalls, 'write_api_returns',
                        lambda *args, **kwargs: None)

    def run_with_new_model_score(score):
        monkeypatch.setattr(fullprocess.scoring, 'score_model', lambda: score)
        run = {'model_version': 1}
        status = fullprocess.run_pipeline(run)
        return status, run, calls

    return run_with_new_model_score


def test_worse_retrained_model_is_not_deployed(pipeline):
    status, run, calls = pipeline(0.50)

    assert status == 'rejected'
    assert 'deploy' not in calls
    assert 'mark_seen' in calls
    assert run['retrained'] is True
    assert run['new_model_score'] == 0.50
    assert run['model_version'] == 1


def test_better_retrained_model_is_deployed(pipeline):
    status, run, calls = pipeline(0.70)

    assert status == 'retrained'
    assert 'deploy' in calls
    assert 'mark_seen' not in calls
    assert run['model_version'] == 2


def test_equally_good_retrained_model_is_deployed(pipeline):
    status, _, calls = pipeline(0.60)

    assert status == 'retrained'
    assert 'deploy' in calls

"""
Module that calls all four endpoints exposed by app.py, combines their outputs,
and writes the combined result to apireturns.txt in output_model_path.
The prediction endpoint is called with /testdata/testdata.csv as input.

Author: Miloš Ćoćić
Date: 12.8.2026.
"""
import json
import os
import requests

with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

output_model_path = config['output_model_path']
test_data_path = config['test_data_path']

API_BASE_URL = os.environ.get('API_BASE_URL', 'http://localhost:8000')

# /diagnostics retrains the model and shells out to pip, so it needs a
# generous timeout; reused everywhere else for simplicity.
REQUEST_TIMEOUT_SECONDS = 120


def call_api_endpoints():
    """
    Call all four API endpoints and return their combined output as a
    dict.
    """
    test_data_file = os.path.join(test_data_path, 'testdata.csv')

    prediction_response = requests.post(
        f'{API_BASE_URL}/prediction',
        params={'filepath': test_data_file},
        timeout=REQUEST_TIMEOUT_SECONDS,
    ).json()
    scoring_response = requests.get(
        f'{API_BASE_URL}/scoring', timeout=REQUEST_TIMEOUT_SECONDS
    ).json()
    summarystats_response = requests.get(
        f'{API_BASE_URL}/summarystats', timeout=REQUEST_TIMEOUT_SECONDS
    ).json()
    diagnostics_response = requests.get(
        f'{API_BASE_URL}/diagnostics', timeout=REQUEST_TIMEOUT_SECONDS
    ).json()

    return {
        'prediction': prediction_response,
        'scoring': scoring_response,
        'summarystats': summarystats_response,
        'diagnostics': diagnostics_response,
    }


def write_api_returns(combined_output, file_name='apireturns.txt'):
    """
    Write the combined endpoint output to `file_name` in
    output_model_path, as pretty-printed JSON.
    """
    os.makedirs(output_model_path, exist_ok=True)
    output_path = os.path.join(output_model_path, file_name)
    with open(output_path, 'w', encoding='utf-8') as output_file:
        json.dump(combined_output, output_file, indent=2)
    return output_path


if __name__ == '__main__':
    write_api_returns(call_api_endpoints())

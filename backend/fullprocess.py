"""
This module is the script of the cron job runs every 10 minutes.
It decides, without any manual intervention, whether the deployed model
needs to be refreshed:

  1. Check for new data: compare the files in input_folder_path against
     the record in prod_deployment_path/ingestedfiles.txt. If there's
     nothing new, stop here.
  2. If there is new data, ingest it (ingestion.py), then check for
     model drift: score the *currently deployed* model against the
     freshly ingested data and compare it (raw comparison) to the score
     that was recorded when it was deployed. If the new score isn't
     lower, the model is still fine -- stop here.
  3. If drift is detected, retrain (training.py) and redeploy
     (deployment.py), then regenerate reporting artifacts
     (confusionmatrix2.png, apireturns2.txt) for the newly deployed
     model.

Author: Miloš Ćoćić
Date: 12.8.2026.
"""
import json
import os
from datetime import datetime
import apicalls
import deployment
import ingestion
import reporting
import scoring
import training

with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

input_folder_path = config['input_folder_path']
output_folder_path = config['output_folder_path']
prod_deployment_path = config['prod_deployment_path']


def get_new_files():
    """
    Return the .csv file names in input_folder_path that aren't
    listed in prod_deployment_path/ingestedfiles.txt.
    """
    ingested_record_path = os.path.join(
        prod_deployment_path, 'ingestedfiles.txt')

    if os.path.exists(ingested_record_path):
        with open(ingested_record_path, 'r', encoding='utf-8') as ingested_file:
            already_ingested = {
                line.strip() for line in ingested_file if line.strip()
            }
    else:
        already_ingested = set()

    current_files = {
        file_name
        for file_name in os.listdir(input_folder_path)
        if file_name.endswith('.csv')
    }

    return sorted(current_files - already_ingested)


def check_for_model_drift():
    """
    Score the currently deployed model against the freshly ingested
    data and compare it to the score it was deployed with. Returns True
    if the new score is lower than the recorded one.
    """
    score_record_path = os.path.join(prod_deployment_path, 'latestscore.txt')
    with open(score_record_path, 'r', encoding='utf-8') as score_file:
        recorded_score = float(score_file.read().strip())

    new_score = scoring.score_model(
        model_dir=prod_deployment_path, test_dir=output_folder_path
    )

    print(f"[fullprocess] Deployed model score was {recorded_score}, "
          f"scores {new_score} on the latest data.")

    return new_score < recorded_score


def main():
    """
    Run all functions in reasonable order.
    """
    new_files = get_new_files()
    if not new_files:
        print("[fullprocess] No new data found. Nothing to do.")
        return

    print(f"[fullprocess] New data found: {new_files}. Ingesting...")
    ingestion.merge_multiple_dataframe()

    if not check_for_model_drift():
        print("[fullprocess] No model drift detected. Keeping the current model.")
        return

    print("[fullprocess] Model drift detected. Retraining and redeploying...")
    training.train_model()
    scoring.score_model()
    deployment.deploy_model()

    print("[fullprocess] Regenerating reporting artifacts for the new model...")
    reporting.plot_confusion_matrix(file_name='confusionmatrix2.png')

    try:
        combined_output = apicalls.call_api_endpoints()
        apicalls.write_api_returns(
            combined_output, file_name='apireturns2.txt')
    except Exception as exc:
        print(
            f"[fullprocess] Skipping apicalls.py (is app.py running?): {exc}")

    print(f"[fullprocess] Done at {datetime.now().isoformat()}.")


if __name__ == '__main__':
    main()

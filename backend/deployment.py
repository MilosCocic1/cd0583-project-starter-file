"""
Module that copies the three artifacts that make up a "deployed model" from their
original locations into the production deployment directory
(prod_deployment_path):

  - trainedmodel.pkl   (from output_model_path)
  - latestscore.txt    (from output_model_path)
  - ingestedfiles.txt  (from output_folder_path)

This script doesn't create any new files, it only copies existing ones.

Author: Miloš Ćoćić
Date: 9.8.2026.
"""
import json
import os
import shutil

with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

output_folder_path = config['output_folder_path']
output_model_path = config['output_model_path']
prod_deployment_path = config['prod_deployment_path']


def deploy_model():
    """
    Copy the trained model, its score, and the ingestion record into
    the production deployment directory.
    """
    os.makedirs(prod_deployment_path, exist_ok=True)

    files_to_copy = [
        (output_model_path, 'trainedmodel.pkl'),
        (output_model_path, 'latestscore.txt'),
        (output_folder_path, 'ingestedfiles.txt'),
    ]

    for source_dir, file_name in files_to_copy:
        shutil.copy(
            os.path.join(source_dir, file_name),
            os.path.join(prod_deployment_path, file_name),
        )

    return prod_deployment_path


if __name__ == '__main__':
    deploy_model()

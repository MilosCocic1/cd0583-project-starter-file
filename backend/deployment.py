"""
Module that copies the three artifacts that make up a "deployed model" from their
original locations into the production deployment directory
(prod_deployment_path):

  - trainedmodel.pkl   (from output_model_path)
  - latestscore.txt    (from output_model_path)
  - ingestedfiles.txt  (from output_folder_path)

It also writes modelversion.txt, a counter that goes up by one on every
deployment, so each deployed model can be identified (v1, v2, ...).

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


def get_model_version():
    """
    Return the version number of the currently deployed model, read
    from prod_deployment_path/modelversion.txt (0 if nothing has been
    deployed yet).
    """
    version_path = os.path.join(prod_deployment_path, 'modelversion.txt')
    if not os.path.exists(version_path):
        return 0
    with open(version_path, 'r', encoding='utf-8') as version_file:
        return int(version_file.read().strip())


def deploy_model():
    """
    Copy the trained model, its score, and the ingestion record into
    the production deployment directory, and bump the model version.
    """
    os.makedirs(prod_deployment_path, exist_ok=True)
    new_version = get_model_version() + 1

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

    with open(
        os.path.join(prod_deployment_path, 'modelversion.txt'), 'w', encoding='utf-8'
    ) as version_file:
        version_file.write(str(new_version))

    return prod_deployment_path


if __name__ == '__main__':
    deploy_model()

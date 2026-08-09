"""
Module reads every .csv file found in the directory specified by
`input_folder_path` in config.json, combines them into a single
de-duplicated pandas DataFrame, and writes:

  - finaldata.csv: the compiled dataset (output_folder_path)
  - ingestedfiles.txt: the list of source file names that were read

Author: Miloš Ćoćić
Date: 9.8.2026.
"""
import json
import os
from datetime import datetime
import pandas as pd
import dbsetup

with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

input_folder_path = config['input_folder_path']
output_folder_path = config['output_folder_path']


def merge_multiple_dataframe():
    """
    Read every csv in input_folder_path, combine and de-dupe them,
    and write finaldata.csv + ingestedfiles.txt to output_folder_path.
    Returns the compiled, de-duplicated DataFrame.
    """
    csv_files = sorted(
        file_name
        for file_name in os.listdir(input_folder_path)
        if file_name.endswith('.csv')
    )

    dataframes = [
        pd.read_csv(os.path.join(input_folder_path, file_name))
        for file_name in csv_files
    ]

    if dataframes:
        final_df = pd.concat(dataframes, ignore_index=True).drop_duplicates()
    else:
        final_df = pd.DataFrame()

    os.makedirs(output_folder_path, exist_ok=True)

    final_df.to_csv(
        os.path.join(
            output_folder_path,
            'finaldata.csv'),
        index=False)

    with open(
        os.path.join(output_folder_path, 'ingestedfiles.txt'), 'w', encoding='utf-8'
    ) as output_file:
        output_file.write('\n'.join(csv_files))

    try:
        dbsetup.log_ingested_files(
            csv_files, input_folder_path, datetime.now())
    except Exception as exc:
        print(
            f"[ingestion] Skipping database logging (MySQL unavailable?): {exc}")

    return final_df


if __name__ == '__main__':
    merge_multiple_dataframe()

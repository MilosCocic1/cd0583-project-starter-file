"""
This module function plot_confusion_matrix() uses diagnostics.model_predictions() against
the test dataset to build a confusion matrix plot, saved as
confusionmatrix.png in output_model_path.
Function plot_time_trends() reads the timing/missing-data history logged to
MySQL by diagnostics.py and plots how they've changed across runs,
saved as timetrends.png in output_model_path.
FUnction generate_pdf_report() bundles the confusion matrix, the time-trend
plot, the model's F1 score, summary
statistics, missing-data diagnostics, dependency versions, and the
list of ingested files into a single PDF, saved as
summaryreport.pdf in output_model_path.

Author: Miloš Ćoćić
Date: 12.8.2026.
"""
import json
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from sklearn.metrics import confusion_matrix

import dbsetup
import diagnostics

with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

output_model_path = config['output_model_path']
output_folder_path = config['output_folder_path']
test_data_path = config['test_data_path']

TARGET_COLUMN = 'exited'


def _read_test_data():
    test_files = [f for f in os.listdir(test_data_path) if f.endswith('.csv')]
    return pd.concat(
        (pd.read_csv(os.path.join(test_data_path, f)) for f in test_files),
        ignore_index=True,
    )


def plot_confusion_matrix(file_name='confusionmatrix.png'):
    """Build a confusion matrix comparing the deployed model's
    predictions on the test data against the actual outcomes, and save
    it as `file_name` in output_model_path.

    `file_name` is overridable so fullprocess.py can save the
    post-automation matrix as confusionmatrix2.png without overwriting
    the one generated during Step 4.
    """
    test_data = _read_test_data()
    actual = test_data[TARGET_COLUMN]
    predicted = diagnostics.model_predictions(test_data)

    matrix = confusion_matrix(actual, predicted)

    fig, ax = plt.subplots(figsize=(6, 5))
    ax.imshow(matrix, cmap='Blues')
    ax.set_xlabel('Predicted label')
    ax.set_ylabel('Actual label')
    ax.set_xticks([0, 1])
    ax.set_yticks([0, 1])
    ax.set_title('Confusion Matrix - Attrition Risk Model')

    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            ax.text(j, i, str(matrix[i, j]), ha='center', va='center', color='black')

    os.makedirs(output_model_path, exist_ok=True)
    output_path = os.path.join(output_model_path, file_name)
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)

    return output_path


def plot_time_trends():
    """Plot ingestion/training timing and per-column NA-percentage
    across every run recorded in the MySQL diagnostics tables, saved as
    timetrends.png in output_model_path.

    Returns the output path, or None if there isn't enough history yet
    (fewer than two runs, or the database is unreachable) to plot a
    trend.
    """
    try:
        timing_rows = dbsetup.get_timing_history()
        missing_rows = dbsetup.get_missing_data_history()
    except Exception as exc:  
        print(f"[reporting] Skipping time-trend plot (MySQL unavailable?): {exc}")
        return None

    if len(timing_rows) < 2 and len(missing_rows) < 2:
        print("[reporting] Not enough history yet to plot time trends.")
        return None

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    if timing_rows:
        timing_df = pd.DataFrame(timing_rows)
        axes[0].plot(timing_df['recorded_at'], timing_df['ingestion_time_seconds'],
                     marker='o', label='Ingestion time (s)')
        axes[0].plot(timing_df['recorded_at'], timing_df['training_time_seconds'],
                     marker='o', label='Training time (s)')
        axes[0].set_title('Pipeline timing over runs')
        axes[0].set_ylabel('Seconds')
        axes[0].tick_params(axis='x', rotation=45)
        axes[0].legend()

    if missing_rows:
        missing_df = pd.DataFrame(missing_rows)
        for column, group in missing_df.groupby('column_name'):
            axes[1].plot(group['recorded_at'], group['na_percent'], marker='o', label=column)
        axes[1].set_title('Missing data (%) over runs')
        axes[1].set_ylabel('NA percent')
        axes[1].tick_params(axis='x', rotation=45)
        axes[1].legend(fontsize='small')

    os.makedirs(output_model_path, exist_ok=True)
    output_path = os.path.join(output_model_path, 'timetrends.png')
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)

    return output_path


def generate_pdf_report():
    """Combine the confusion matrix, the F1 score, summary statistics,
    missing-data diagnostics, dependency versions, the ingested-files
    record, and (when available) the time-trend plot into a single PDF
    report, saved as summaryreport.pdf in output_model_path."""
    confusion_matrix_path = plot_confusion_matrix()
    time_trends_path = plot_time_trends()

    with open(
        os.path.join(output_model_path, 'latestscore.txt'), 'r', encoding='utf-8'
    ) as score_file:
        f1_score_text = score_file.read().strip()

    ingested_files_path = os.path.join(output_folder_path, 'ingestedfiles.txt')
    if os.path.exists(ingested_files_path):
        with open(ingested_files_path, 'r', encoding='utf-8') as ingested_files_handle:
            ingested_files = ingested_files_handle.read().strip()
    else:
        ingested_files = 'ingestedfiles.txt not found'

    summary_stats = diagnostics.dataframe_summary()
    missing = diagnostics.missing_data()
    finaldata_columns = pd.read_csv(
        os.path.join(output_folder_path, 'finaldata.csv')
    ).columns.tolist()
    dependencies = diagnostics.outdated_packages_list()

    os.makedirs(output_model_path, exist_ok=True)
    output_path = os.path.join(output_model_path, 'summaryreport.pdf')

    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    story = [
        Paragraph('Attrition Risk Model - Summary Report', styles['Title']),
        Spacer(1, 0.2 * inch),
        Paragraph(f'<b>Latest F1 score:</b> {f1_score_text}', styles['Normal']),
        Paragraph(f'<b>Ingested files:</b> {ingested_files}', styles['Normal']),
        Spacer(1, 0.2 * inch),
        Paragraph('Confusion Matrix', styles['Heading2']),
        Image(confusion_matrix_path, width=4 * inch, height=3.3 * inch),
        Spacer(1, 0.2 * inch),
        Paragraph('Summary Statistics', styles['Heading2']),
    ]

    summary_table_data = [['Column', 'Mean', 'Median', 'Mode', 'Std']] + [
        [
            row['column'],
            f"{row['mean']:.2f}",
            f"{row['median']:.2f}",
            f"{row['mode']:.2f}" if row['mode'] is not None else 'N/A',
            f"{row['std']:.2f}",
        ]
        for row in summary_stats
    ]
    story.append(_styled_table(summary_table_data))
    story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph('Missing Data (% NA per column)', styles['Heading2']))
    missing_table_data = [['Column', 'NA %']] + [
        [col, f'{pct:.2f}'] for col, pct in zip(finaldata_columns, missing)
    ]
    story.append(_styled_table(missing_table_data))
    story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph('Dependencies', styles['Heading2']))
    dependency_table_data = [list(dependencies.columns)] + dependencies.values.tolist()
    story.append(_styled_table(dependency_table_data))

    if time_trends_path:
        story.append(Spacer(1, 0.2 * inch))
        story.append(Paragraph('Time Trends', styles['Heading2']))
        story.append(Image(time_trends_path, width=6.5 * inch, height=2.7 * inch))

    doc.build(story)

    return output_path


def _styled_table(data):
    table = Table(data, hAlign='LEFT')
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F2F2F2')]),
    ]))
    return table


if __name__ == '__main__':
    plot_confusion_matrix()
    generate_pdf_report()

"""

Module that would instead of writing pipeline results to .csv/.txt files,
mirrors the important records (ingested files, model scores, and
diagnostics) into a MySQL database, using the mysql-connector-python
module.
Connection settings are read from environment variables so no database
credentials need to live in config.json or in source control:

    DB_HOST      default "localhost"
    DB_PORT      default 3306
    DB_USER      default "root"
    DB_PASSWORD  default "" (empty)
    DB_NAME      default "risk_system"

Author: Miloš Ćoćić
Date: 9.8.2026.
"""
import os
import mysql.connector
from mysql.connector import Error as MySQLError


def get_db_config():
    """
    Read MySQL connection settings
    from environment variables, falling back to local defaults.
    """
    return {
        "host": os.environ.get("DB_HOST", "localhost"),
        "port": int(os.environ.get("DB_PORT", "3306")),
        "user": os.environ.get("DB_USER", "root"),
        "password": os.environ.get("DB_PASSWORD", ""),
    }


DB_NAME = os.environ.get("DB_NAME", "risk_system")


def get_connection(use_database=True):
    """Open a new connection to the MySQL server."""
    config = get_db_config()
    if use_database:
        config["database"] = DB_NAME
    return mysql.connector.connect(**config)


def create_database():
    """Create the project database if it doesn't already exist."""
    conn = get_connection(use_database=False)
    try:
        cursor = conn.cursor()
        cursor.execute(
            f"CREATE DATABASE IF NOT EXISTS {DB_NAME} "
            "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
        conn.commit()
        cursor.close()
    finally:
        conn.close()


TABLE_STATEMENTS = {
    "ingested_files": """
        CREATE TABLE IF NOT EXISTS ingested_files (
            id INT AUTO_INCREMENT PRIMARY KEY,
            file_name VARCHAR(255) NOT NULL,
            source_folder VARCHAR(255) NOT NULL,
            recorded_at DATETIME NOT NULL
        )
    """,
    "model_scores": """
        CREATE TABLE IF NOT EXISTS model_scores (
            id INT AUTO_INCREMENT PRIMARY KEY,
            f1_score FLOAT NOT NULL,
            dataset_source VARCHAR(255) NOT NULL,
            recorded_at DATETIME NOT NULL
        )
    """,
    "diagnostics_timing": """
        CREATE TABLE IF NOT EXISTS diagnostics_timing (
            id INT AUTO_INCREMENT PRIMARY KEY,
            ingestion_time_seconds FLOAT NOT NULL,
            training_time_seconds FLOAT NOT NULL,
            recorded_at DATETIME NOT NULL
        )
    """,
    "diagnostics_missing_data": """
        CREATE TABLE IF NOT EXISTS diagnostics_missing_data (
            id INT AUTO_INCREMENT PRIMARY KEY,
            column_name VARCHAR(255) NOT NULL,
            na_percent FLOAT NOT NULL,
            recorded_at DATETIME NOT NULL
        )
    """,
    "diagnostics_summary_stats": """
        CREATE TABLE IF NOT EXISTS diagnostics_summary_stats (
            id INT AUTO_INCREMENT PRIMARY KEY,
            column_name VARCHAR(255) NOT NULL,
            mean_value FLOAT NOT NULL,
            median_value FLOAT NOT NULL,
            mode_value FLOAT NULL,
            std_value FLOAT NOT NULL,
            recorded_at DATETIME NOT NULL
        )
    """,
}

COLUMN_MIGRATIONS = [
    (
        "diagnostics_summary_stats",
        "mode_value",
        "ALTER TABLE diagnostics_summary_stats "
        "ADD COLUMN mode_value FLOAT NULL AFTER median_value",
    ),
]


def _apply_migrations(cursor):
    for table_name, column_name, alter_statement in COLUMN_MIGRATIONS:
        cursor.execute(
            "SELECT COUNT(*) FROM information_schema.columns "
            "WHERE table_schema = %s AND table_name = %s AND column_name = %s",
            (DB_NAME, table_name, column_name),
        )
        (column_exists,) = cursor.fetchone()
        if not column_exists:
            cursor.execute(alter_statement)


def create_tables():
    """
    Create every project table if it doesn't already exist, and apply
    any pending migrations to tables that already existed.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        for statement in TABLE_STATEMENTS.values():
            cursor.execute(statement)
        _apply_migrations(cursor)
        conn.commit()
        cursor.close()
    finally:
        conn.close()


def setup_database():
    """Full setup: create the database, then create all tables."""
    create_database()
    create_tables()


def log_ingested_files(file_names, source_folder, recorded_at):
    """Insert one row per ingested file name into ingested_files."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.executemany(
            "INSERT INTO ingested_files (file_name, source_folder, recorded_at) "
            "VALUES (%s, %s, %s)", [
                (name, source_folder, recorded_at) for name in file_names], )
        conn.commit()
        cursor.close()
    finally:
        conn.close()


def log_model_score(f1_score, dataset_source, recorded_at):
    """Insert one row into model_scores for a scoring run."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO model_scores (f1_score, dataset_source, recorded_at) "
            "VALUES (%s, %s, %s)",
            (f1_score, dataset_source, recorded_at),
        )
        conn.commit()
        cursor.close()
    finally:
        conn.close()


def log_timing(ingestion_time_seconds, training_time_seconds, recorded_at):
    """Insert one row into diagnostics_timing for an execution_time() run."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO diagnostics_timing "
            "(ingestion_time_seconds, training_time_seconds, recorded_at) "
            "VALUES (%s, %s, %s)",
            (ingestion_time_seconds, training_time_seconds, recorded_at),
        )
        conn.commit()
        cursor.close()
    finally:
        conn.close()


def log_missing_data(column_percentages, recorded_at):
    """Dict mapping column name."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.executemany(
            "INSERT INTO diagnostics_missing_data (column_name, na_percent, recorded_at) "
            "VALUES (%s, %s, %s)", [
                (col, pct, recorded_at) for col, pct in column_percentages.items()], )
        conn.commit()
        cursor.close()
    finally:
        conn.close()


def log_summary_stats(stats_records, recorded_at):
    """List of dicts with keys column, mean, median, mode, std."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.executemany(
            "INSERT INTO diagnostics_summary_stats "
            "(column_name, mean_value, median_value, mode_value, std_value, recorded_at) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            [
                (r["column"], r["mean"], r["median"], r.get("mode"), r["std"], recorded_at)
                for r in stats_records
            ],
        )
        conn.commit()
        cursor.close()
    finally:
        conn.close()


def get_timing_history(limit=100):
    """Return up to `limit` diagnostics_timing rows, oldest first."""
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT ingestion_time_seconds, training_time_seconds, recorded_at "
            "FROM diagnostics_timing ORDER BY recorded_at ASC LIMIT %s", (limit,), )
        rows = cursor.fetchall()
        cursor.close()
        return rows
    finally:
        conn.close()


def get_missing_data_history(limit=500):
    """Return up to `limit` diagnostics_missing_data rows, oldest first."""
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT column_name, na_percent, recorded_at "
            "FROM diagnostics_missing_data ORDER BY recorded_at ASC LIMIT %s",
            (limit,),
        )
        rows = cursor.fetchall()
        cursor.close()
        return rows
    finally:
        conn.close()


if __name__ == "__main__":
    try:
        setup_database()
        print(f"Database '{DB_NAME}' and tables are ready.")
    except MySQLError as exc:
        print(f"Could not set up the database: {exc}")
        raise

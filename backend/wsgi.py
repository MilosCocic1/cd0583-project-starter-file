"""
Module with entry point for running app.py under a production WSGI server (gunicorn):

    gunicorn --bind 0.0.0.0:8000 wsgi:app

Author: Miloš Ćoćić
Date: 12.8.2026.
"""
from app import app

if __name__ == '__main__':
    app.run()

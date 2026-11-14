"""
Shared pytest setup. The backend modules read config.json and their data
folders relative to the working directory, so the tests run from the
backend folder no matter where pytest is started.
"""
import os
import sys

import pytest

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(BACKEND_DIR)
sys.path.insert(0, BACKEND_DIR)

from app import app as flask_app  # noqa: E402  (needs the chdir above)


@pytest.fixture
def client():
    flask_app.config['TESTING'] = True
    with flask_app.test_client() as test_client:
        yield test_client

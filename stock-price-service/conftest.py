"""
Root conftest: set required env vars before any app module is imported.
This file is processed by pytest before test collection begins.
"""
import os

os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test_db")

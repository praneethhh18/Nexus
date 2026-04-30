"""
Pytest collection hooks for NexusAgent.

Isolation rule: tests MUST NOT touch the live Postgres database. Each test
fixture sets its own DB_PATH to a tmp SQLite file. To enforce this, we strip
DATABASE_URL from the environment at MODULE LOAD time of conftest, which
happens before pytest collects any test files. By the time any test code or
production module imports `config.db`, DATABASE_URL is already gone, so the
abstraction falls back to SQLite (the tmp file each test sets up).

A test that explicitly wants to exercise the Postgres path can monkeypatch
DATABASE_URL back in for the duration of that test only.
"""
from __future__ import annotations

import os

# Run at conftest module load — fires before any test or production import.
# We can't simply pop the var: config/settings.py calls load_dotenv() at import,
# which would re-inject DATABASE_URL from .env. Setting it to empty string
# here is a sentinel that load_dotenv won't override (because the var IS set,
# just empty), and config.db.backend() treats empty as "SQLite" since it's not
# a postgres:// URL.
os.environ["DATABASE_URL"] = ""

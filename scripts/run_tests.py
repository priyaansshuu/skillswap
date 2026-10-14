"""Run migrations and tests only against an explicitly named test database."""

import os
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.engine import make_url

root = Path(__file__).resolve().parents[1]
load_dotenv(root / ".env")
url = os.environ.get("TEST_DATABASE_URL")
if not url or not make_url(url).database.endswith("_test"):
    raise SystemExit(
        "Set TEST_DATABASE_URL to a disposable PostgreSQL database whose name ends in _test"
    )
env = os.environ.copy()
env["DATABASE_URL"] = url
subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], cwd=root, env=env, check=True)
raise SystemExit(
    subprocess.call([sys.executable, "-m", "pytest", "-q", *sys.argv[1:]], cwd=root, env=env)
)

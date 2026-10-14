"""Run the UI checks against an isolated local PostgreSQL database.

Never truncates the demo database. Requires the demo .env and installed frontend
dependencies. Credentials are passed through the child environment, not arguments.
"""

import os
import secrets
import shutil
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import urlopen

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

ROOT = Path(__file__).resolve().parents[1]


def wait_for(url, process):
    for _ in range(150):
        if process.poll() is not None:
            raise RuntimeError(
                "A browser-check server stopped. Check frontend/test-results/server.log."
            )
        try:
            with urlopen(url, timeout=1) as response:
                if response.status == 200:
                    return
        except OSError:
            time.sleep(0.2)
    raise RuntimeError("Timed out waiting for the isolated browser-check server.")


def main():
    load_dotenv(ROOT / ".env")
    source = make_url(os.environ["DATABASE_URL"])
    if source.host not in {"127.0.0.1", "localhost"}:
        raise RuntimeError("Browser checks require a local PostgreSQL server.")
    database = "skillswap_browser_test"
    admin_engine = create_engine(
        source.set(database="postgres"), isolation_level="AUTOCOMMIT", hide_parameters=True
    )
    with admin_engine.connect() as conn:
        if not conn.scalar(
            text("SELECT 1 FROM pg_database WHERE datname=:name"), {"name": database}
        ):
            conn.execute(text('CREATE DATABASE "skillswap_browser_test"'))
    admin_engine.dispose()
    os.environ["DATABASE_URL"] = source.set(database=database).render_as_string(hide_password=False)
    os.environ["DEMO_PASSWORD"] = secrets.token_urlsafe(24)
    os.environ["SKILLSWAP_E2E_PASSWORD"] = os.environ["DEMO_PASSWORD"]
    os.environ["SKILLSWAP_FRONTEND_URL"] = "http://127.0.0.1:8001"
    os.environ["SKILLSWAP_API_URL"] = "http://127.0.0.1:8001"
    sys.path.insert(0, str(ROOT))
    os.chdir(ROOT)
    from alembic.config import Config

    from alembic import command

    command.upgrade(Config(str(ROOT / "alembic.ini")), "head")
    from app.database import get_engine

    assert make_url(os.environ["DATABASE_URL"]).database == database
    with get_engine().begin() as conn:
        conn.execute(text("TRUNCATE users, skills RESTART IDENTITY CASCADE"))
        conn.execute(text("TRUNCATE auth_attempts"))
    from app.cli import seed

    seed(blank_members=2)
    frontend = ROOT / "frontend"
    node = shutil.which("node")
    if not node:
        raise RuntimeError("Install Node.js before running browser checks.")
    log_dir = frontend / "test-results"
    log_dir.mkdir(exist_ok=True)
    processes = []
    with (log_dir / "server.log").open("w", encoding="utf-8") as log:
        try:
            api = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "uvicorn",
                    "app.main:app",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    "8001",
                ],
                cwd=ROOT,
                stdout=log,
                stderr=log,
                env=os.environ.copy(),
            )
            processes.append(api)
            wait_for("http://127.0.0.1:8001/health/ready", api)
            if not (frontend / "dist/index.html").is_file():
                raise RuntimeError("Run npm run build in frontend/ before browser checks.")
            args = sys.argv[1:] or ["e2e"]
            return subprocess.call(
                [node, str(frontend / "node_modules/@playwright/test/cli.js"), "test", *args],
                cwd=frontend,
                env=os.environ.copy(),
            )
        finally:
            for process in reversed(processes):
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
            get_engine().dispose()


if __name__ == "__main__":
    raise SystemExit(main())

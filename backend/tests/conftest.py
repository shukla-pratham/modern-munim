"""
backend/tests/conftest.py

Session-scoped isolated PostgreSQL container for Modern Munim backend tests.

Design guarantees:
  - All os.environ test overrides are applied at module import time, before
    any app.* module is imported.  pydantic-settings v2 gives os.environ
    priority over .env file values, so Settings() will read the test URL
    regardless of what backend/.env contains.
  - The application engine (app.core.database.engine) and SessionLocal are
    built exactly once, during the first import of app.core.database, which
    is triggered by test-module collection after conftest module-level code
    has already set DATABASE_URL.  No post-import replacement is performed.
  - alembic/env.py line 19 derives sqlalchemy.url from settings.DATABASE_URL;
    because settings is imported (and cached) after os.environ is set, it
    already holds the test URL.  The AlembicConfig sqlalchemy.url placeholder
    from alembic.ini is overwritten by env.py to settings.DATABASE_URL, which
    is the test URL.  No extra set_main_option call is needed or used.
  - Container identity is established by capturing the exact container ID
    returned by `docker run --detach`.  All subsequent operations (readiness
    poll, psql, stop) target that ID, not the name, wherever possible.
  - A unique ownership label (munim.test.run=<session-uuid>) is applied at
    container creation.  Before any cleanup the label is verified.
  - Cleanup runs unconditionally in a finally block.  Failures are reported
    clearly.  Nothing is silently ignored.
  - If the process is interrupted before the container ID is captured, the
    recovery procedure (printed to stdout) describes identity verification
    before any manual removal.
  - No existing container, volume, database, or Compose resource is touched.
"""
from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
import uuid
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# STEP 1: Set environment variables BEFORE any app.* import.
#
# conftest.py module-level code executes before pytest collects and imports
# test modules.  test_admin_auth.py's module-level `from app.core.database
# import SessionLocal` therefore runs AFTER these assignments, so
# app.core.config.Settings() reads DATABASE_URL from os.environ → test URL.
# ---------------------------------------------------------------------------

_CONTAINER     = "munim_test_pg"
_DB_NAME       = "munim_test"
_DB_USER       = "munim_test"
_DB_PASS       = "munim_test_pass"   # throwaway, non-secret, test-only
_HOST          = "127.0.0.1"
_PORT          = "15432"
_PG_IMAGE      = "postgres:15-alpine"
_SESSION_UUID  = uuid.uuid4().hex        # unique label for this test run
_OWNERSHIP_LABEL = f"munim.test.run={_SESSION_UUID}"

_TEST_DB_URL = (
    f"postgresql://{_DB_USER}:{_DB_PASS}@{_HOST}:{_PORT}/{_DB_NAME}"
)

BACKEND_ROOT = Path(__file__).resolve().parents[1]

# These module-level assignments happen before any app.* import:
os.environ["DATABASE_URL"]      = _TEST_DB_URL
os.environ["SECRET_KEY"]        = "munim-test-only-not-production-secret-" + "x" * 32
os.environ["ENVIRONMENT"]       = "development"   # disables all production guards
os.environ["EMAIL_OTP_DEV_LOG"] = "true"
os.environ["CORS_ORIGINS"]      = "http://localhost:3000"
os.environ["ALLOWED_HOSTS"]     = "localhost,127.0.0.1"
# No app.* imports at module level below this line.

# ---------------------------------------------------------------------------
# STEP 2: Subprocess helpers (stdlib only)
# ---------------------------------------------------------------------------

def _run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a subprocess.  Never prints secrets."""
    return subprocess.run(cmd, capture_output=True, text=True, check=check)


def _container_exists(name: str) -> bool:
    return _run(
        ["docker", "inspect", "--type=container", name], check=False
    ).returncode == 0


def _port_in_use(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        return s.connect_ex((host, port)) == 0


def _wait_ready(container_id: str, timeout: int = 30) -> None:
    """Poll pg_isready inside the container until it accepts connections."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        r = _run(
            [
                "docker", "exec", container_id,
                "pg_isready", "-U", _DB_USER, "-d", "postgres",
            ],
            check=False,
        )
        if r.returncode == 0:
            return
        time.sleep(1)
    raise RuntimeError(
        f"Container {container_id[:12]!r} not ready after {timeout}s.\n"
        f"Inspect logs: docker logs {container_id[:12]}"
    )


def _verify_label(container_id: str) -> bool:
    """Return True iff the container carries our session ownership label."""
    r = _run(
        [
            "docker", "inspect", container_id,
            "--format", "{{range $k,$v := .Config.Labels}}{{$k}}={{$v}}\n{{end}}",
        ],
        check=False,
    )
    return _OWNERSHIP_LABEL in r.stdout


# ---------------------------------------------------------------------------
# STEP 3: Session-scoped fixture
# ---------------------------------------------------------------------------

# Module-level slot for the captured container ID.
# Empty string means docker run has not yet succeeded.
_captured_id: list[str] = [""]   # mutable container so finally block can read it


@pytest.fixture(scope="session", autouse=True)
def isolated_test_database():   # noqa: C901
    """Create an ephemeral PostgreSQL container, migrate, run tests, destroy."""

    # ── Preflight ──────────────────────────────────────────────────────────
    if _container_exists(_CONTAINER):
        pytest.exit(
            f"\nPREFLIGHT ABORT: Container '{_CONTAINER}' already exists.\n"
            "Identify it before taking any action:\n"
            f"  docker inspect {_CONTAINER} "
            "--format '{{.Config.Image}} {{range $k,$v := .Config.Labels}}"
            "{{$k}}={{$v}} {{end}}'\n"
            "Remove ONLY if it is a confirmed stale test container "
            f"(image={_PG_IMAGE}, label prefix munim.test.run=):\n"
            f"  docker rm -f {_CONTAINER}\n"
            "No resource was created or modified.",
            returncode=3,
        )

    if _port_in_use(_HOST, int(_PORT)):
        pytest.exit(
            f"\nPREFLIGHT ABORT: Port {_PORT} on {_HOST} is already in use.\n"
            "No resource was created or modified.",
            returncode=3,
        )

    # ── Start ephemeral container ──────────────────────────────────────────
    # --rm:    auto-remove container layer on stop
    # --tmpfs: data directory in RAM only; zero disk persistence; no volume
    # --label: ownership fingerprint for safe identification
    run_result = _run([
        "docker", "run",
        "--rm",
        "--detach",
        "--name",   _CONTAINER,
        "-e",       f"POSTGRES_USER={_DB_USER}",
        "-e",       f"POSTGRES_PASSWORD={_DB_PASS}",
        "-e",       "POSTGRES_DB=postgres",
        "-p",       f"{_HOST}:{_PORT}:5432",
        "--tmpfs",  "/var/lib/postgresql/data:rw,noexec,nosuid,size=256m",
        "--label",  _OWNERSHIP_LABEL,
        _PG_IMAGE,
    ])
    _captured_id[0] = run_result.stdout.strip()   # 64-char SHA256 ID

    try:
        # ── Readiness ─────────────────────────────────────────────────────
        _wait_ready(_captured_id[0], timeout=30)

        # ── Create test database ───────────────────────────────────────────
        # Use psql inside the container via captured ID — no host connection yet.
        _run([
            "docker", "exec", _captured_id[0],
            "psql", "-U", _DB_USER, "-d", "postgres",
            "-c", f"CREATE DATABASE {_DB_NAME};",
        ])

        # ── Run Alembic migrations ─────────────────────────────────────────
        # At this point app.core.config has been imported (by test_admin_auth.py
        # module-level imports, triggered by pytest collection which happened
        # after conftest module-level code set os.environ["DATABASE_URL"]).
        # settings.DATABASE_URL = _TEST_DB_URL (already cached).
        # env.py line 19 will write settings.DATABASE_URL into the Alembic
        # config object, so migrations target munim_test@127.0.0.1:15432.
        from alembic.config import Config as AlembicConfig
        from alembic import command as alembic_cmd

        # Use the actual alembic.ini so script_location resolves correctly.
        # cwd=backend/ so the relative path works.
        alembic_cfg = AlembicConfig(file_=str(BACKEND_ROOT / "alembic.ini"))
        alembic_cmd.upgrade(alembic_cfg, "head")

        # ── Yield: tests execute ───────────────────────────────────────────
        yield

    finally:
        # ── Teardown ──────────────────────────────────────────────────────
        cid = _captured_id[0]
        if not cid:
            # docker run never succeeded; nothing to clean up.
            print(
                "\n[conftest] No container ID captured. "
                "If a container named '{_CONTAINER}' exists, identify it:\n"
                f"  docker inspect {_CONTAINER} "
                "--format '{{.Config.Image}} {{range $k,$v := .Config.Labels}}"
                "{{$k}}={{$v}} {{end}}'\n"
                f"Remove ONLY if label contains munim.test.run=.\n"
            )
            return

        # Verify ownership before touching anything.
        if not _verify_label(cid):
            print(
                f"\n[conftest] TEARDOWN SAFETY: Container {cid[:12]} does not "
                f"carry the expected ownership label '{_OWNERSHIP_LABEL}'.\n"
                "This container was NOT created by this test run. "
                "It will NOT be removed automatically.\n"
                f"Inspect manually: docker inspect {cid[:12]}"
            )
            return

        stop_result = _run(["docker", "stop", cid], check=False)

        if stop_result.returncode != 0:
            print(
                f"\n[conftest] TEARDOWN WARNING: 'docker stop {cid[:12]}' "
                f"returned {stop_result.returncode}.\n"
                f"stderr: {stop_result.stderr.strip()}\n"
                "Manual recovery — ONLY after confirming identity:\n"
                f"  docker inspect {cid[:12]} --format '{{{{.Config.Image}}}}'\n"
                f"  # Must show: {_PG_IMAGE}\n"
                f"  docker rm -f {cid[:12]}\n"
            )
        else:
            # --rm should have removed the container after stop.
            inspect_result = _run(
                ["docker", "inspect", "--type=container", _CONTAINER],
                check=False,
            )
            if inspect_result.returncode == 0:
                print(
                    f"\n[conftest] TEARDOWN WARNING: '{_CONTAINER}' still "
                    "present after stop (--rm may not have fired).\n"
                    "Manual removal — only after confirming identity:\n"
                    f"  docker inspect {_CONTAINER} "
                    "--format '{{{{.Config.Image}}}} "
                    "{{{{range $k,$v := .Config.Labels}}}}{{{{$k}}}}={{{{$v}}}} "
                    "{{{{end}}}}'\n"
                    f"  docker rm -f {_CONTAINER}\n"
                )

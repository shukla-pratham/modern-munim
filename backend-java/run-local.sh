#!/usr/bin/env bash
# Run Spring Boot using the existing backend/.env (shared DB + SECRET_KEY).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="${ROOT}/backend/.env"
if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing $ENV_FILE — copy from backend/.env.example first." >&2
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

# Spring expects optional JDBC pieces; DataSourceConfig normalizes SQLAlchemy URLs.
export SERVER_PORT="${SERVER_PORT:-8080}"
export BCRYPT_STRENGTH="${BCRYPT_STRENGTH:-12}"

cd "${ROOT}/backend-java"
exec mvn -q spring-boot:run

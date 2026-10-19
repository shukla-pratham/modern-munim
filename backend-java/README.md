# Modern Munim — Spring Boot Backend

Java 21 / Spring Boot 3.4 business API (migration in progress).

## Run locally

```bash
# Uses backend/.env (DATABASE_URL + SECRET_KEY shared with FastAPI)
./run-local.sh
```

Listens on **http://127.0.0.1:8080**

- Health: `GET /health`
- Swagger: `http://127.0.0.1:8080/swagger-ui.html`
- Migrated routes: `/api/products`, `/api/inventory`, `/api/auth`

## Tests

```bash
mvn test
```

## Docs

See repo-root [MIGRATION.md](../MIGRATION.md) and [ARCHITECTURE.md](../ARCHITECTURE.md).

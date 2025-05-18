# Project Database Workflow

This document describes how to use **DBML** as the source of truth for your database schema, generate SQL, reverse-engineer Django models, and keep everything in sync.

## Directory Structure

```
.
├── docker-compose.yml        # Infrastructure: Postgres, Redis, etc.
├── .env                      # Environment variables (DATABASE_URL, secrets)
├── manage.py                 # Django project entrypoint
├── jobboard_project/         # Django project settings, URLs, WSGI/ASGI
│   └── ...
├── src/
│   └── job_market_tools/     # Django app
│       ├── db_schema/        # Source-of-truth schema artifacts
│       │   ├── database.dbml
│       │   └── schema.sql    # Generated SQL DDL
│       ├── models/           # Django models (split by domain)
│       ├── scraper/          # Existing scraping code
│       ├── fixtures/         # JSON/YAML fixtures for lookup tables
│       ├── management/       # Custom Django management commands
│       └── services/         # Helper modules (dedupe, analytics)
└── pyproject.toml            # Python dependencies and project config
```

## Prerequisites

* **Node.js** (for the DBML CLI)
* **Python 3.x** with Django installed (via Poetry or pip)
* **Docker & Docker Compose** (to spin up Postgres locally)

## 1. Generate SQL from DBML

Install the DBML CLI and convert your `database.dbml` into Postgres DDL:

```bash
npm install -g @dbml/cli

dbml2sql src/job_market_tools/db_schema/database.dbml --postgres > src/job_market_tools/db_schema/schema.sql
```

## 2. Apply the SQL to a Temporary Database

Use Docker Compose to bring up the `db` service and apply the schema:

```bash
docker-compose up -d db

docker-compose exec db \
  psql -U postgres -d your_db_name -f src/job_market_tools/db_schema/schema.sql
```

## 3. Reverse-Engineer Django Models

1. Configure `DATABASES` in `jobboard_project/settings.py` to point at the sandbox database.
2. Run Django's inspectdb to dump models:

   ```bash
   python manage.py inspectdb --database default --include-partitions --include-views > src/job_market_tools/models/db_models.py
   ```
3. Review `db_models.py`—it contains all tables as Django model stubs.

## 4. Refine and Organize Models

* **Split** classes from `db_models.py` into domain files under `models/`:

  * `company.py` for `Company`, `Offer`, etc.
  * `lookup.py` for lookup tables (`Skills`, `Languages`, etc.)
  * `location.py` for `Location`, `Country`, etc.

* **Remove** any `Meta.managed = False` to let Django manage migrations.

* **Adjust** field options (`null=True`, `blank=True`), add `__str__()` methods, indexes, and verbose names as needed.

## 5. Create and Run Migrations

```bash
python manage.py makemigrations job_market_tools
python manage.py migrate
```

## 6. Load Lookup Fixtures

Place JSON/YAML fixtures in `src/job_market_tools/fixtures/`, e.g. `countries.json`, then load:

```bash
python manage.py loaddata countries.json
```

## Ongoing Workflow

Whenever `database.dbml` changes:

1. Repeat **Steps 1–3** to regenerate `schema.sql`, reapply to sandbox DB, and inspect models.
2. **Merge** schema/model changes into your existing files in `models/`.
3. Run `makemigrations` & `migrate` to apply updates to your development database.
4. Update or add fixtures if new lookup values are introduced.

---
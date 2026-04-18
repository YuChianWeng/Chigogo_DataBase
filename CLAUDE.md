# ChitoGo DataBase Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-04-16

## Active Technologies

- **001-place-data-service**: Python 3.11+, FastAPI, SQLAlchemy 2.x, PostgreSQL 12, psycopg2-binary, pydantic-settings, uvicorn

## Project Structure

```text
app/
├── main.py
├── db.py
├── core/config.py
├── models/          # Place, PlaceSourceGoogle, PlaceFeatures ORM models
├── routers/         # health.py, places.py
└── services/        # ingestion.py

scripts/
└── seed.py

specs/
└── 001-place-data-service/   # spec, plan, research, data-model, contracts
```

## Commands

```bash
# Install
pip install -r requirements.txt

# Run service (auto-creates tables on startup)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Seed sample data
python scripts/seed.py

# Health check
curl http://localhost:8000/api/v1/health/db

# District filter verification
curl "http://localhost:8000/api/v1/places?district=中正區"
```

## Code Style

- Python: follow PEP 8; SQLAlchemy 2.x `DeclarativeBase` style
- pydantic-settings v2: use `model_config` dict (not inner `Config` class)
- All models must be imported in `app/models/__init__.py` before `create_all`
- Use `JSONB` from `sqlalchemy.dialects.postgresql` for nested/variable fields
- Naming convention: `chitogo_` prefix for DB user/database

## Database

- Host: localhost:5432
- Database: chitogo
- User: chitogo_user
- URL: `postgresql://chitogo_user:kawairoha@localhost:5432/chitogo`
- Schema management: `Base.metadata.create_all()` on startup (Alembic deferred)

## Recent Changes

- 001-place-data-service: Initial plan — place data service with ingestion, normalization, storage, retrieval
- 001-place-data-service: Seed/verification flow aligned to Taipei sample place `華山1914文化創意產業園區`

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->

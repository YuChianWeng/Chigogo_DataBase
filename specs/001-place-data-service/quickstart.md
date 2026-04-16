# Quickstart: Place Data Service

**Branch**: `001-place-data-service`
**Database**: `postgresql://chitogo_user:kawairoha@localhost:5432/chitogo`

---

## Prerequisites

- Python 3.11+
- PostgreSQL 12 running locally with `chitogo` database and `chitogo_user` credentials

---

## Setup

```bash
# 1. Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. (Optional) Create .env to override DATABASE_URL
echo "DATABASE_URL=postgresql://chitogo_user:kawairoha@localhost:5432/chitogo" > .env
```

---

## Run the service

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Tables are created automatically on startup via `Base.metadata.create_all()`.

---

## Seed sample data

```bash
python scripts/seed.py
```

Expected output:
```
[seed] Connecting to database...
[seed] Tables verified.
[seed] Inserted place: Shibuya Crossing (id=1)
[seed] Inserted raw source row for google_place_id=ChIJN1t_tDeuEmsRUsoyG83frY4
[seed] Done.
```

If already seeded:
```
[seed] Place already exists: Shibuya Crossing — skipping.
[seed] Done.
```

---

## Verify endpoints

```bash
# DB health check
curl http://localhost:8000/api/v1/health/db

# List all places
curl http://localhost:8000/api/v1/places

# Filter by district
curl "http://localhost:8000/api/v1/places?district=Shibuya"

# Filter by type and min rating
curl "http://localhost:8000/api/v1/places?primary_type=tourist_attraction&min_rating=4.0"

# Get place detail
curl http://localhost:8000/api/v1/places/1

# Import a place via HTTP
curl -X POST http://localhost:8000/api/v1/places/import/google \
  -H "Content-Type: application/json" \
  -d '{
    "payload": {
      "id": "ChIJN1t_tDeuEmsRUsoyG83frY4",
      "displayName": { "text": "Shibuya Crossing" },
      "primaryType": "tourist_attraction",
      "formattedAddress": "2-chome Dogenzaka, Shibuya City, Tokyo",
      "location": { "latitude": 35.6595, "longitude": 139.7004 },
      "rating": 4.6,
      "userRatingCount": 82341,
      "businessStatus": "OPERATIONAL"
    }
  }'
```

---

## Verification checklist

- [ ] `GET /api/v1/health/db` returns `{"status": "ok", "database": "connected"}`
- [ ] `python scripts/seed.py` completes without error
- [ ] `GET /api/v1/places` returns at least one place record
- [ ] `GET /api/v1/places/1` returns full place detail
- [ ] `POST /api/v1/places/import/google` with a new payload returns `"action": "created"`
- [ ] Re-submitting the same `google_place_id` returns `"action": "updated"` (no duplicate)
- [ ] `GET /api/v1/places?district=Shibuya` returns only Shibuya places

---

## Interactive API docs

```
http://localhost:8000/docs
```

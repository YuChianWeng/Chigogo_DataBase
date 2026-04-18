# Chito-Go Place Data Service

## What This Service Does

Chito-Go Place Data Service is a standalone FastAPI + PostgreSQL service for place data ingestion, normalization, storage, and retrieval.

This repository is the data service layer only. It is designed to be called later by another backend service.

Current responsibilities:

- Ingest place data
- Normalize place records
- Store normalized and raw source data
- Retrieve stored place data through HTTP APIs

## What This Service Does NOT Do

This service is not the full Chito-Go travel assistant product.

It does not currently implement:

- Trip planning or itinerary generation
- Recommendation orchestration
- User accounts or authentication
- Frontend UI
- Full Google Places API crawling pipeline
- Background job processing
- Complex ranking or recommendation logic

## Current Features

Currently implemented:

- PostgreSQL integration
- FastAPI app startup with table creation on startup
- DB health check endpoint
- `places` table for normalized place records
- `place_source_google` table for raw Google Places payloads
- `place_features` table for optional derived scores
- `GET /api/v1/places`
- `GET /api/v1/places/{place_id}`
- `GET /api/v1/health/db`
- `POST /api/v1/places/import/google`
- `scripts/import_place.py`
- `scripts/seed.py`
- `scripts/fetch_google_nearby.py` — Google Nearby Search fetch + import pipeline
- `config/google_seed_targets.json` — all 12 Taipei district seed points and POI type groups
- Taipei district name normalization (Chinese and English forms) with cross-boundary filtering
- Unit test suite under `tests/`

Verified sample seed place:

- Name: `華山1914文化創意產業園區`
- District: `中正區`

## Tech Stack

- Python
- FastAPI
- Uvicorn
- SQLAlchemy 2.x
- PostgreSQL
- `psycopg2-binary`
- `pydantic-settings`

## Project Structure

```text
.
├── app/
│   ├── core/
│   │   └── config.py
│   ├── models/
│   │   ├── place.py
│   │   ├── place_features.py
│   │   └── place_source_google.py
│   ├── routers/
│   │   ├── health.py
│   │   └── places.py
│   ├── schemas/
│   │   └── place.py
│   ├── services/
│   │   └── ingestion.py
│   ├── db.py
│   └── main.py
├── config/
│   └── google_seed_targets.json
├── scripts/
│   ├── fetch_google_nearby.py
│   ├── import_place.py
│   └── seed.py
├── tests/
│   ├── test_fetch_google_nearby.py
│   └── test_ingestion.py
├── specs/
├── .env.example
├── requirements.txt
└── README.md
```

## Prerequisites

Before running locally, make sure you have:

- Python 3.11+ available
- PostgreSQL running locally
- A database named `chitogo`
- A PostgreSQL user matching the local default connection string
- `psql` installed for the verification commands in this README

Local default database connection currently used by the app:

```text
postgresql://chitogo_user:kawairoha@localhost:5432/chitogo
```

## Local Setup

Clone the repository, move into the project directory, and follow the steps below.

## Create and Activate `.venv`

Use the exact commands below:

```bash
~/QuantTrade/backend/.venv/bin/python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

## Install Dependencies

```bash
python -m pip install -r requirements.txt
```

## Configure Environment Variables

This project reads configuration from `.env`.

Create a local `.env` file from `.env.example` and set the database URL if needed.

Example:

```env
DATABASE_URL=postgresql://chitogo_user:kawairoha@localhost:5432/chitogo
```

Notes:

- The current local default is `postgresql://chitogo_user:kawairoha@localhost:5432/chitogo`
- If `.env` is missing, the app still defaults to that same local PostgreSQL URL

## Run the App

The app was verified locally on port `8800`.

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8800
```

On startup, the app creates tables from the SQLAlchemy models using `Base.metadata.create_all(...)`.

## Verify DB Connection

Check that the app can reach PostgreSQL:

```bash
curl http://localhost:8800/api/v1/health/db
```

Expected response:

```json
{
  "status": "ok",
  "database": "connected"
}
```

You can also verify that the tables exist:

```bash
psql "postgresql://chitogo_user:kawairoha@localhost:5432/chitogo" -c '\dt'
```

## Seed Sample Data

Run the seed script:

```bash
python scripts/seed.py
python scripts/seed.py
```

Running it twice is intentional and useful:

- The normalized `places` row should remain a single logical place for the same `google_place_id`
- The raw `place_source_google` table should receive an additional append-only row on each import

Verify row counts:

```bash
psql "postgresql://chitogo_user:kawairoha@localhost:5432/chitogo" -c "SELECT count(*) FROM places WHERE google_place_id = 'ChIJH8B5JxapQjQR3KX8A2Q9V4o';"
psql "postgresql://chitogo_user:kawairoha@localhost:5432/chitogo" -c "SELECT count(*) FROM place_source_google WHERE google_place_id = 'ChIJH8B5JxapQjQR3KX8A2Q9V4o';"
```

Expected behavior after seeding twice:

- `places` count for that `google_place_id` should remain `1`
- `place_source_google` count for that `google_place_id` should increase with each import

## API Endpoints Summary

### `GET /api/v1/health/db`

Checks database connectivity.

### `GET /api/v1/places`

Returns a list of normalized places.

Currently supported query parameters:

- `district`
- `primary_type`
- `indoor`
- `budget_level`
- `min_rating`
- `limit`
- `offset`

### `GET /api/v1/places/{place_id}`

Returns detailed information for a single normalized place record, including optional derived features if present.

### `POST /api/v1/places/import/google`

Imports one Google-style place payload into the service.

Behavior:

- Stores a raw append-only record in `place_source_google`
- Creates or updates the normalized row in `places` by `google_place_id`
- Optionally creates or updates a `place_features` row if `features` are provided

## Example curl Commands

### Health check

```bash
curl http://localhost:8800/api/v1/health/db
```

### List places

```bash
curl http://localhost:8800/api/v1/places
```

### Filter by district

When filtering with Chinese text, test with URL encoding:

```bash
curl --get "http://localhost:8800/api/v1/places" --data-urlencode "district=中正區"
```

### Get place detail

```bash
curl http://localhost:8800/api/v1/places/1
```

### Import a place payload

```bash
curl -X POST "http://localhost:8800/api/v1/places/import/google" \
  -H "Content-Type: application/json" \
  -d @payload.json
```

## Fetch and Import from Google Nearby Search

`scripts/fetch_google_nearby.py` queries the Google Places Nearby Search API for each configured Taipei district and imports results directly into the local data service.

### Prerequisites

- A valid Google Maps API key with Places API (New) enabled
- The data service running locally on port 8800

### Usage

```bash
# Run all 12 Taipei districts
GOOGLE_MAPS_API_KEY=<your_key> python scripts/fetch_google_nearby.py

# Run a single district
GOOGLE_MAPS_API_KEY=<your_key> python scripts/fetch_google_nearby.py --district 中正區

# Include lower-priority bus station queries
GOOGLE_MAPS_API_KEY=<your_key> python scripts/fetch_google_nearby.py --include-secondary-transport
```

### Configuration

`config/google_seed_targets.json` defines:

- **`poi_type_groups`** — named groups of Google place types to query (attractions, food, shopping, lodging, transport, etc.)
- **`districts`** — all 12 Taipei districts, each with 3+ geographic seed points and radius settings

Place results whose district does not match a known Taipei district are stored as raw payloads only and are not inserted into the normalized `places` table.

### Output

The script prints per-query stats and a final summary:

```
[中正區] seed=huashan group=food_drink mode=includedTypes type=restaurant google_returned=20 imported=18 skipped_non_taipei=2 failed=0
[summary] districts=1 type_groups=6 queries=18 google_returned=200 imported=175 skipped_non_taipei=20 failed=5
```

Exit code is `0` on full success and `1` if any query fails.

## Running Tests

```bash
python -m pytest tests/
```

The test suite covers:

- `test_ingestion.py` — district normalization, Taipei filtering, and ingestion behavior using a fake DB session
- `test_fetch_google_nearby.py` — config loading and district/type group structure validation

## Example Import JSON Payload

The import endpoint expects a request body with this shape:

```json
{
  "payload": {
    "id": "ChIJH8B5JxapQjQR3KX8A2Q9V4o",
    "displayName": {
      "text": "華山1914文化創意產業園區"
    },
    "primaryType": "tourist_attraction",
    "types": [
      "tourist_attraction",
      "cultural_landmark",
      "event_venue",
      "point_of_interest",
      "establishment"
    ],
    "formattedAddress": "10058台灣台北市中正區八德路一段1號",
    "addressComponents": [
      {
        "longText": "10058",
        "shortText": "10058",
        "types": ["postal_code"],
        "languageCode": "zh-TW"
      },
      {
        "longText": "台灣",
        "shortText": "TW",
        "types": ["country", "political"],
        "languageCode": "zh-TW"
      },
      {
        "longText": "台北市",
        "shortText": "台北市",
        "types": ["administrative_area_level_1", "political"],
        "languageCode": "zh-TW"
      },
      {
        "longText": "中正區",
        "shortText": "中正區",
        "types": ["sublocality", "political"],
        "languageCode": "zh-TW"
      },
      {
        "longText": "八德路一段1號",
        "shortText": "1號",
        "types": ["route"],
        "languageCode": "zh-TW"
      }
    ],
    "location": {
      "latitude": 25.0440581,
      "longitude": 121.5298485
    },
    "rating": 4.4,
    "userRatingCount": 12000,
    "businessStatus": "OPERATIONAL",
    "googleMapsUri": "https://maps.google.com/?cid=4342178518828401116",
    "websiteUri": "https://www.huashan1914.com/",
    "nationalPhoneNumber": "+886 2 2358 1914",
    "currentOpeningHours": {
      "openNow": true,
      "weekdayDescriptions": [
        "星期一: 09:30 – 21:00",
        "星期二: 09:30 – 21:00",
        "星期三: 09:30 – 21:00",
        "星期四: 09:30 – 21:00",
        "星期五: 09:30 – 21:00",
        "星期六: 09:30 – 21:00",
        "星期日: 09:30 – 21:00"
      ]
    }
  },
  "features": {
    "culture_score": 0.95,
    "photo_score": 0.88,
    "family_score": 0.72,
    "feature_json": {
      "source": "manual-example"
    }
  }
}
```

If you want to use the CLI import script instead of the HTTP endpoint, provide the raw place payload only:

```bash
python scripts/import_place.py payload_raw.json
```

Where `payload_raw.json` contains just the Google-style payload object, not the outer `{"payload": ...}` wrapper.

## Data Model Overview

### `places`

Stores normalized place records used for retrieval.

Important characteristics:

- One normalized row per `google_place_id`
- `google_place_id` is unique
- Contains normalized fields such as name, type, district, address, coordinates, rating, contact info, and opening hours
- Also includes optional service-level fields such as `indoor`, `outdoor`, `budget_level`, `trend_score`, and `confidence_score`

### `place_source_google`

Stores raw Google Places payloads exactly as ingested.

Important characteristics:

- Append-only by design
- Keeps the original payload in `raw_json`
- Multiple rows may exist for the same `google_place_id`
- Can link back to a normalized `places.id` when a normalized record exists

### `place_features`

Stores optional derived or downstream scores for a place.

Important characteristics:

- One row per `place_id`
- Optional
- Intended for derived scores such as `couple_score`, `family_score`, `photo_score`, `food_score`, and related feature metadata

## Notes About Append-Only Raw Payload Behavior

This project intentionally separates normalized storage from raw source history.

Current behavior:

- `places` stores the latest normalized representation of a place
- `place_source_google` stores append-only raw payload snapshots
- Re-importing the same `google_place_id` should update the normalized row in `places`
- Re-importing the same `google_place_id` should append another raw row in `place_source_google`

This means:

- Normalized place rows should not duplicate by `google_place_id`
- Raw source rows are expected to grow over time on re-import
- Seed/import verification should check both tables, not just one

## Known Limitations / Not Yet Implemented

Current limitations based on the implemented code:

- No Alembic or migration workflow yet
- No authentication or authorization
- No delete or update endpoints for places
- No background ingestion jobs or queue processing
- No external Google Places API fetch client in this repo
- No deduplication strategy beyond unique normalized rows by `google_place_id`
- No versioned raw payload retention policy, pruning, or archival process
- No advanced search, sorting, or full-text querying
- No response pagination metadata beyond `limit` and `offset`

## Suggested Next Steps

- Add Alembic migrations for schema management
- Add automated tests for ingestion, retrieval, and database behavior
- Add validation rules around required source payload fields
- Add structured logging for imports and DB errors
- Add import idempotency tests that verify one normalized row and multiple raw rows
- Add more filter options and explicit sort controls on `GET /api/v1/places`
- Add support for bulk import workflows
- Add clearer API docs and example responses for downstream backend integration
- Add a formal contract for how the future backend will call this service

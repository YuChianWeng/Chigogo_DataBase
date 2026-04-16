# Tasks: Place Data Service

**Input**: Design documents from `specs/001-place-data-service/`
**Prerequisites**: plan.md ✓ spec.md ✓ research.md ✓ data-model.md ✓ contracts/api.md ✓ quickstart.md ✓

**Tests**: Not included — no TDD requirement in spec. Verification is via seed script + curl commands per quickstart.md.

**Organization**: Tasks grouped by user story. Each phase is an independently testable increment.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no shared dependencies)
- **[US#]**: Maps to user story from spec.md (US1=P1, US2=P2, US3=P3, US4=P4)
- All task descriptions include exact file paths

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the project skeleton. All directories, stub files, and dependency declarations. No logic yet.

- [ ] T001 Create project directory structure: `app/`, `app/core/`, `app/models/`, `app/routers/`, `app/services/`, `app/schemas/`, `scripts/` — add empty `__init__.py` to each `app/` subdirectory
- [ ] T002 Create `requirements.txt` with pinned dependencies: `fastapi>=0.111.0`, `uvicorn[standard]>=0.29.0`, `sqlalchemy>=2.0.0`, `psycopg2-binary>=2.9.9`, `pydantic-settings>=2.2.0`
- [ ] T003 [P] Create `.env.example` at repo root with `DATABASE_URL=postgresql://chitogo_user:kawairoha@localhost:5432/chitogo`

**Checkpoint**: `pip install -r requirements.txt` succeeds. Directory tree matches plan.md structure.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. All three ORM models and the app entry point live here.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T004 Implement `app/core/config.py` — `Settings(BaseSettings)` class with `DATABASE_URL` default `"postgresql://chitogo_user:kawairoha@localhost:5432/chitogo"`; use `model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}`; export `settings = Settings()`
- [ ] T005 Implement `app/db.py` — `create_engine(settings.DATABASE_URL, pool_pre_ping=True)`, `SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)`, `class Base(DeclarativeBase): pass`, `get_db()` generator yielding `SessionLocal()` with `finally: db.close()`
- [ ] T006 [P] Implement `app/models/place.py` — `Place` ORM model: `id` Integer PK autoincrement; `google_place_id` String(255) unique+NOT NULL+indexed; `display_name` String(512) NOT NULL; `normalized_name` String(512) nullable; `primary_type` String(128) nullable+indexed; `types_json` JSONB nullable; `formatted_address` String(1024) nullable; `district` String(255) nullable+indexed; `latitude`/`longitude` Numeric(10,7) nullable; `rating` Numeric(3,1) nullable; `user_rating_count` Integer nullable; `price_level` String(64) nullable; `business_status` String(64) nullable; `google_maps_uri`/`website_uri` String(1024) nullable; `national_phone_number` String(32) nullable; `opening_hours_json` JSONB nullable; `indoor`/`outdoor` Boolean nullable; `budget_level` String(32) nullable+indexed; `trend_score`/`confidence_score` Numeric(5,4) nullable; `created_at` DateTime(timezone=True) server_default=func.now(); `updated_at` DateTime(timezone=True) server_default=func.now() onupdate=func.now(); `last_synced_at` DateTime(timezone=True) nullable; relationships: `source_records` (one-to-many PlaceSourceGoogle), `features` (one-to-one PlaceFeatures uselist=False)
- [ ] T007 [P] Implement `app/models/place_source_google.py` — `PlaceSourceGoogle` ORM model: `id` Integer PK autoincrement; `place_id` Integer ForeignKey("places.id") NOT NULL+indexed; `google_place_id` String(255) NOT NULL+indexed (denormalized); `raw_json` JSONB NOT NULL; `fetched_at` DateTime(timezone=True) server_default=func.now(); relationship: `place` back_populates="source_records"
- [ ] T008 [P] Implement `app/models/place_features.py` — `PlaceFeatures` ORM model: `place_id` Integer ForeignKey("places.id") `primary_key=True` (no separate id); `couple_score`, `family_score`, `photo_score`, `food_score`, `culture_score`, `rainy_day_score`, `crowd_score`, `transport_score`, `hidden_gem_score` all Numeric(5,4) nullable; `feature_json` JSONB nullable; `updated_at` DateTime(timezone=True) server_default=func.now() onupdate=func.now(); relationship: `place` back_populates="features"
- [ ] T009 Implement `app/models/__init__.py` — import `Place`, `PlaceSourceGoogle`, `PlaceFeatures` from their respective modules; export `__all__`; this file MUST be imported before `Base.metadata.create_all()` is called
- [ ] T010 Implement `app/main.py` — `FastAPI(title="ChitoGo Place Data Service", version="0.1.0", lifespan=lifespan)`; `lifespan` async context manager: `import app.models` (registers all models) then `Base.metadata.create_all(bind=engine)` then `yield`; `app.include_router(health.router, prefix="/api/v1", tags=["health"])`; `app.include_router(places.router, prefix="/api/v1", tags=["places"])`; import health and places routers (files created as stubs in T001, filled in Phase 3–5)

**Checkpoint**: `uvicorn app.main:app --reload` starts without import errors. Tables created in PostgreSQL on first run (verify with `psql chitogo -c "\dt"`).

---

## Phase 3: User Story 1 — Query Normalized Place Data (Priority: P1) 🎯 MVP

**Goal**: Downstream backends can retrieve a filtered list of normalized places and fetch full detail for any single place.

**Independent Test**: Pre-seed one place record via `scripts/seed.py` (Phase 6), then confirm `GET /api/v1/places` returns a non-empty list and `GET /api/v1/places/1` returns full detail.

### Implementation for User Story 1

- [ ] T011 [P] [US1] Define Pydantic response schemas in `app/schemas/place.py` — `PlaceFeaturesOut` (all 9 score fields Optional[float], feature_json Optional[dict], updated_at Optional[datetime]); `PlaceListItem` (id, google_place_id, display_name, Optional primary_type, Optional district, Optional formatted_address, Optional rating, Optional indoor, Optional outdoor, Optional budget_level, Optional trend_score); `PlaceDetail` (all Place fields as Optional where nullable + `features: Optional[PlaceFeaturesOut]`); configure `model_config = {"from_attributes": True}` on all schemas
- [ ] T012 [US1] Implement `GET /api/v1/places` in `app/routers/places.py` — query `Place` table via `db.query(Place)`; apply optional filters: `district` (string eq), `primary_type` (string eq), `indoor` (bool), `budget_level` (string eq), `min_rating` (float, `Place.rating >= min_rating`); apply `limit` (default 50, max 200) and `offset` (default 0); return `list[PlaceListItem]` (use `response_model=list[PlaceListItem]`)
- [ ] T013 [US1] Implement `GET /api/v1/places/{place_id}` in `app/routers/places.py` — fetch `Place` by `id`; raise `HTTPException(404)` if not found; fetch `PlaceFeatures` by `place_id` (separate query); assemble and return `PlaceDetail` with `features` block populated or `None`

**Checkpoint**: `GET /api/v1/places` returns `[]` (empty list, not error). After seed (Phase 6), returns one record. `GET /api/v1/places/1` returns full detail. `GET /api/v1/places/999` returns 404.

---

## Phase 4: User Story 2 — Ingest Google Places Data (Priority: P2)

**Goal**: An operator or pipeline can submit a raw Google Places payload via HTTP POST or CLI and have it normalized, stored, and immediately queryable.

**Independent Test**: `POST /api/v1/places/import/google` with a sample payload returns `"action": "created"`. Re-submitting the same payload returns `"action": "updated"`. `GET /api/v1/places` shows the ingested record. `place_source_google` table has one new row per submission.

### Implementation for User Story 2

- [ ] T014 [P] [US2] Implement field mapping helpers in `app/services/ingestion.py` — `_safe_get(d: dict, *keys, default=None)`: traverses nested dicts safely returning default on any non-dict intermediate; `_normalize_name(name: str) -> str`: `unicodedata.normalize("NFKC", name).lower().strip()`; `_extract_district(payload: dict) -> str | None`: iterate `payload.get("addressComponents", [])`, return `component.get("longText")` for first entry with `"sublocality"` or `"locality"` in its `types`, else `None`
- [ ] T015 [US2] Implement `ingest_google_place(db: Session, payload: dict, features: dict | None = None) -> dict` in `app/services/ingestion.py` — (1) extract `google_place_id = payload.get("id")`; raise `ValueError("google_place_id is required")` if missing; (2) build `PlaceSourceGoogle(google_place_id=..., raw_json=payload, fetched_at=now)` but do NOT add to session yet; (3) extract `display_name` via `_safe_get(payload, "displayName", "text") or payload.get("displayName")`; if missing or not a string: add raw record, commit, return `{"google_place_id": ..., "action": "raw_only", "detail": "..."}` ; (4) build `place_data` dict mapping all fields using `_safe_get` and `payload.get` with `None` defaults; (5) `existing = db.query(Place).filter_by(google_place_id=google_place_id).first()`; if exists: `setattr` all fields, `action = "updated"`; else: `place = Place(**place_data)`, `db.add(place)`, `action = "created"`; (6) `db.flush()` to get `place.id`; (7) `raw_record.place_id = place.id`, `db.add(raw_record)`; (8) if `features`: query existing `PlaceFeatures` by `place_id`, update with `setattr` if found or create new filtering to known column keys; (9) `db.commit()`, `db.refresh(place)`, return `{"place_id": place.id, "google_place_id": ..., "action": action}`
- [ ] T016 [US2] Implement `POST /api/v1/places/import/google` in `app/routers/places.py` — Pydantic request body `GoogleImportRequest(payload: dict, features: dict | None = None)`; call `ingestion.ingest_google_place(db, request.payload, request.features)`; catch `ValueError` and raise `HTTPException(status_code=422, detail=str(e))`; return `ImportResult(place_id: int | None, google_place_id: str, action: str)` defined in `app/schemas/place.py`
- [ ] T017 [US2] Implement `scripts/import_place.py` — CLI script: `sys.path` setup for repo root; parse single argument as path to a JSON file; read and `json.load` the file; create `SessionLocal()`; call `ingestion.ingest_google_place(db, payload)`; print JSON result; close session; exit 0

**Checkpoint**: `POST /api/v1/places/import/google` with full payload returns `{"action": "created"}`. Re-POST returns `{"action": "updated"}`. `python scripts/import_place.py sample.json` prints result to stdout. `place_source_google` table has 2 rows for the same `google_place_id` after two submissions (append-only confirmed).

---

## Phase 5: User Story 3 — Monitor Service Health (Priority: P3)

**Goal**: A developer or infrastructure tool can confirm the service is running and the database is reachable with a single endpoint call.

**Independent Test**: `GET /api/v1/health/db` returns `{"status": "ok", "database": "connected"}` when DB is up. Returns 503 with error body when DB is unreachable.

### Implementation for User Story 3

- [ ] T018 [US3] Implement `GET /api/v1/health/db` in `app/routers/health.py` — `router = APIRouter()`; endpoint: `Depends(get_db)`; execute `db.execute(text("SELECT 1"))`; return `{"status": "ok", "database": "connected"}` on success; catch any `Exception` and return `JSONResponse(status_code=503, content={"status": "error", "database": "unreachable", "detail": str(e)})`

**Checkpoint**: `curl http://localhost:8000/api/v1/health/db` returns `{"status":"ok","database":"connected"}`.

---

## Phase 6: User Story 4 — Seed Place Data for Development (Priority: P4)

**Goal**: A developer can run a single script to populate the database with a representative place record and immediately verify the full ingest → store → retrieve round-trip.

**Independent Test**: `python scripts/seed.py` succeeds and prints confirmation. Running it a second time does NOT create a duplicate `places` row (idempotent). `GET /api/v1/places/1` returns the seeded record.

### Implementation for User Story 4

- [ ] T019 [US4] Implement `scripts/seed.py` — `sys.path` setup for repo root; `import app.models` (registers models); `Base.metadata.create_all(bind=engine)`; define `SAMPLE_GOOGLE_PAYLOAD` dict with full Shibuya Crossing data (`id`, `displayName.text`, `primaryType`, `types`, `formattedAddress`, `location.latitude/longitude`, `rating`, `userRatingCount`, `businessStatus`, `googleMapsUri`); create `SessionLocal()`; call `ingest_google_place(db, SAMPLE_GOOGLE_PAYLOAD)`; print `"[seed] Inserted place: {display_name} (id={place_id})"` if action is `"created"`, or `"[seed] Place already exists: {display_name} — skipping."` if `"updated"`; always print confirmation that raw source row was appended; print `"[seed] Done."`; close session
- [ ] T020 [US4] Verify seed idempotency and round-trip in `scripts/seed.py` — run `python scripts/seed.py` once (should print "Inserted"); run again (should print "already exists"); confirm `places` table has exactly 1 row for `ChIJN1t_tDeuEmsRUsoyG83frY4`; confirm `place_source_google` has 2 rows (one per run — append-only); confirm `GET /api/v1/places/1` returns the seeded record

**Checkpoint**: Both verification confirmations pass. Place detail endpoint shows the seeded Shibuya Crossing record with all mapped fields.

---

## Final Phase: Polish & Cross-Cutting Concerns

**Purpose**: End-to-end verification and cleanup before handoff.

- [ ] T021 Run full verification checklist from `specs/001-place-data-service/quickstart.md` — execute all 7 verification steps: DB health check, seed success, list endpoint returns record, detail endpoint returns full record, import endpoint returns `"created"`, re-import returns `"updated"`, district filter returns only Shibuya records
- [ ] T022 [P] Review `CLAUDE.md` and confirm all listed commands match the actual implementation; update any discrepancies in run commands, file paths, or database config

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1: Setup         → no dependencies, start immediately
Phase 2: Foundational  → depends on Phase 1 ⚠️ BLOCKS all user stories
Phase 3: US1           → depends on Phase 2 completion
Phase 4: US2           → depends on Phase 2 completion (can run parallel with US1 if staffed)
Phase 5: US3           → depends on Phase 2 completion (can run parallel with US1, US2)
Phase 6: US4           → depends on Phase 4 completion (seed uses ingestion service)
Final:   Polish        → depends on all user story phases complete
```

### User Story Dependencies

- **US1 (P1)**: Unblocked after Phase 2. Needs: `Place` model, `get_db`, Pydantic schemas.
- **US2 (P2)**: Unblocked after Phase 2. Needs: `Place`, `PlaceSourceGoogle`, `PlaceFeatures` models. Independent of US1.
- **US3 (P3)**: Unblocked after Phase 2. Needs only `get_db`. Fully independent of US1 and US2.
- **US4 (P4)**: Depends on US2 (calls `ingest_google_place`). No dependency on US1 or US3.

### Within Each User Story

- Helpers before service logic (T014 before T015)
- Service logic before HTTP endpoint (T015 before T016)
- HTTP endpoint before CLI script (T016 before T017)
- Models before schemas (T006–T008 before T011)

---

## Parallel Opportunities

### Phase 2 (Foundational) — can run T006, T007, T008 in parallel:

```
Start simultaneously:
  T006: app/models/place.py
  T007: app/models/place_source_google.py
  T008: app/models/place_features.py
Then sequentially:
  T009: app/models/__init__.py  (depends on T006, T007, T008)
  T010: app/main.py             (depends on T009)
```

### Phase 3 (US1) — T011 can run in parallel with T012 start:

```
Start simultaneously:
  T011: app/schemas/place.py   (Pydantic schemas)
Then:
  T012: GET /api/v1/places     (depends on T011)
  T013: GET /api/v1/places/{id} (depends on T011)
```

### Phases 3, 5 in parallel (if two developers):

```
Developer A: Phase 3 (US1 — retrieval endpoints)
Developer B: Phase 5 (US3 — health endpoint, single task T018)
```

### Phases 3, 4, 5 in parallel (if three developers):

```
Developer A: Phase 3 (US1)
Developer B: Phase 4 (US2 — ingestion)
Developer C: Phase 5 (US3 — health, T018 only)
```

---

## Implementation Strategy

### MVP: User Story 1 Only (retrieval)

1. Phase 1: Setup
2. Phase 2: Foundational (T004–T010)
3. Phase 3: US1 (T011–T013)
4. **STOP**: Seed one record manually via `POST /import/google`, verify `GET /places` and `GET /places/1`
5. Confirm retrieval is working before building ingestion

### Incremental Delivery

1. Phase 1 + Phase 2 → app starts, tables created
2. Phase 3 (US1) → retrieval endpoints live
3. Phase 4 (US2) → ingestion live; data can now flow in
4. Phase 5 (US3) → health endpoint live; service is monitorable
5. Phase 6 (US4) → seed script ready; local dev is fully bootstrapped
6. Final phase → verified and ready for consumption by downstream backend

---

## Task Summary

| Phase | Tasks | Story | Parallelizable |
|---|---|---|---|
| Phase 1: Setup | T001–T003 | — | T003 [P] |
| Phase 2: Foundational | T004–T010 | — | T006, T007, T008 [P] |
| Phase 3: US1 (P1) | T011–T013 | US1 | T011 [P] |
| Phase 4: US2 (P2) | T014–T017 | US2 | T014 [P] |
| Phase 5: US3 (P3) | T018 | US3 | — |
| Phase 6: US4 (P4) | T019–T020 | US4 | — |
| Final: Polish | T021–T022 | — | T022 [P] |
| **Total** | **22 tasks** | | **6 parallelizable** |

---

## Notes

- `[P]` tasks operate on different files with no shared pending dependencies — safe to run concurrently
- `[US#]` label maps each task to its user story for traceability and independent validation
- The `app/models/__init__.py` (T009) import chain is critical — missing it causes silent table-creation failures
- `place_features.place_id` must be declared `primary_key=True` (not just a FK) — missing this causes an ORM mapping error
- `pool_pre_ping=True` on the engine (T005) silently handles stale connections — do not remove
- `place_source_google` rows are append-only by design — re-importing the same place will always add a new raw row; this is expected behavior, not a bug
- Commit after each task group to maintain clean git history (auto-commit hook is enabled)

import unicodedata
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.place import Place
from app.models.place_features import PlaceFeatures
from app.models.place_source_google import PlaceSourceGoogle


def _safe_get(d: dict, *keys, default=None):
    current = d
    for key in keys:
        if not isinstance(current, dict):
            return default
        if key not in current:
            return default
        current = current[key]
    return current


def _normalize_name(name: str) -> str:
    return unicodedata.normalize("NFKC", name).lower().strip()


def _extract_district(payload: dict) -> str | None:
    for component in payload.get("addressComponents", []):
        types = component.get("types", [])
        if "sublocality" in types or "locality" in types:
            return component.get("longText")
    return None


def ingest_google_place(
    db: Session, payload: dict, features: dict | None = None
) -> dict:
    google_place_id = payload.get("id")
    if not google_place_id:
        raise ValueError("google_place_id is required")

    raw_record = PlaceSourceGoogle(
        google_place_id=google_place_id,
        raw_json=payload,
        fetched_at=datetime.now(timezone.utc),
    )

    display_name = _safe_get(payload, "displayName", "text") or payload.get("displayName")
    if not display_name or not isinstance(display_name, str):
        db.add(raw_record)
        db.commit()
        return {
            "place_id": None,
            "google_place_id": google_place_id,
            "action": "raw_only",
        }

    place_data = {
        "google_place_id": google_place_id,
        "display_name": display_name,
        "normalized_name": _normalize_name(display_name),
        "primary_type": payload.get("primaryType"),
        "types_json": payload.get("types"),
        "formatted_address": payload.get("formattedAddress"),
        "district": _extract_district(payload),
        "latitude": _safe_get(payload, "location", "latitude"),
        "longitude": _safe_get(payload, "location", "longitude"),
        "rating": payload.get("rating"),
        "user_rating_count": payload.get("userRatingCount"),
        "price_level": payload.get("priceLevel"),
        "business_status": payload.get("businessStatus"),
        "google_maps_uri": payload.get("googleMapsUri"),
        "website_uri": payload.get("websiteUri"),
        "national_phone_number": payload.get("nationalPhoneNumber"),
        "opening_hours_json": payload.get("currentOpeningHours"),
        "last_synced_at": datetime.now(timezone.utc),
    }

    existing = db.query(Place).filter_by(google_place_id=google_place_id).first()
    if existing:
        place = existing
        for key, value in place_data.items():
            setattr(place, key, value)
        action = "updated"
    else:
        place = Place(**place_data)
        db.add(place)
        action = "created"

    db.flush()

    raw_record.place_id = place.id
    db.add(raw_record)

    if features is not None:
        known_feature_keys = {
            "couple_score",
            "family_score",
            "photo_score",
            "food_score",
            "culture_score",
            "rainy_day_score",
            "crowd_score",
            "transport_score",
            "hidden_gem_score",
            "feature_json",
        }
        feature_data = {k: v for k, v in features.items() if k in known_feature_keys}
        existing_features = db.query(PlaceFeatures).filter_by(place_id=place.id).first()
        if existing_features:
            for key, value in feature_data.items():
                setattr(existing_features, key, value)
        else:
            db.add(PlaceFeatures(place_id=place.id, **feature_data))

    db.commit()
    db.refresh(place)

    return {
        "place_id": place.id,
        "google_place_id": google_place_id,
        "action": action,
    }

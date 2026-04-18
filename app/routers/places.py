from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.place import Place
from app.models.place_features import PlaceFeatures
from app.schemas.place import (
    GoogleImportRequest,
    ImportResult,
    PlaceDetail,
    PlaceFeaturesOut,
    PlaceListItem,
)
from app.services.ingestion import ingest_google_place

router = APIRouter()


@router.get("/places", response_model=list[PlaceListItem])
def list_places(
    district: str | None = None,
    primary_type: str | None = None,
    indoor: bool | None = None,
    budget_level: str | None = None,
    min_rating: float | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(Place)

    if district is not None:
        query = query.filter(Place.district == district)
    if primary_type is not None:
        query = query.filter(Place.primary_type == primary_type)
    if indoor is not None:
        query = query.filter(Place.indoor == indoor)
    if budget_level is not None:
        query = query.filter(Place.budget_level == budget_level)
    if min_rating is not None:
        query = query.filter(Place.rating >= min_rating)

    return query.offset(offset).limit(limit).all()


@router.get("/places/{place_id}", response_model=PlaceDetail)
def get_place(place_id: int, db: Session = Depends(get_db)):
    place = db.query(Place).filter(Place.id == place_id).first()
    if place is None:
        raise HTTPException(status_code=404, detail="Place not found")

    features = db.query(PlaceFeatures).filter(PlaceFeatures.place_id == place_id).first()
    detail = PlaceDetail.model_validate(place)
    if features is None:
        return detail
    return detail.model_copy(update={"features": PlaceFeaturesOut.model_validate(features)})


@router.post("/places/import/google", response_model=ImportResult)
def import_google_place(
    request: GoogleImportRequest, db: Session = Depends(get_db)
):
    try:
        result = ingest_google_place(db, request.payload, request.features)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return result

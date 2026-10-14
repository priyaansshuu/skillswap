import time
from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import func, select

from app.errors import require
from app.matching import ALGORITHMS, rank_candidates
from app.models import ExchangeRequest, ExchangeSession, Review
from app.security import AdminUser, Db

router = APIRouter(prefix="/admin/evaluation", tags=["Evaluation"])


class EvaluationCandidate(BaseModel):
    provider_id: str
    offered_skill_id: str
    score: float
    factors: dict[str, float]
    suggested_start: datetime
    hierarchy_distance: int


class ModelEvaluation(BaseModel):
    algorithm: str
    elapsed_ms: float
    weights: dict[str, float]
    candidates: list[EvaluationCandidate]


class Comparison(BaseModel):
    request_id: str
    models: list[ModelEvaluation]
    caveat: str


class Outcomes(BaseModel):
    invited_requests: int
    scheduled_sessions: int
    completed_sessions: int
    acceptance_rate: float | None
    completion_rate: float | None
    mean_review_stars: float | None
    review_count: int
    caveat: str


def compare_models(db, item):
    results = []
    for algorithm in ALGORITHMS:
        started = time.perf_counter()
        candidates, weights = rank_candidates(db, item, algorithm)
        results.append(
            ModelEvaluation(
                algorithm=algorithm,
                elapsed_ms=round((time.perf_counter() - started) * 1000, 3),
                weights=weights,
                candidates=candidates[:10],
            )
        )
    return Comparison(
        request_id=item.id,
        models=results,
        caveat="Local query timings and rankings are descriptive. Synthetic data does not establish recommendation quality. Precision@K requires supplied relevance labels.",
    )


@router.get("/requests/{request_id}", response_model=Comparison)
def compare_request(request_id: str, db: Db, admin: AdminUser):
    item = db.get(ExchangeRequest, request_id)
    require(item is not None, "REQUEST_NOT_FOUND", "Request does not exist", 404)
    return compare_models(db, item)


@router.get("/outcomes", response_model=Outcomes)
def outcomes(db: Db, admin: AdminUser):
    invited = db.scalar(
        select(func.count())
        .select_from(ExchangeRequest)
        .where(ExchangeRequest.provider_id.is_not(None))
    )
    scheduled = db.scalar(select(func.count()).select_from(ExchangeSession))
    completed = db.scalar(
        select(func.count())
        .select_from(ExchangeSession)
        .where(ExchangeSession.status == "COMPLETED")
    )
    reviews, mean = db.execute(select(func.count(Review.id), func.avg(Review.stars))).one()
    return Outcomes(
        invited_requests=invited,
        scheduled_sessions=scheduled,
        completed_sessions=completed,
        acceptance_rate=scheduled / invited if invited else None,
        completion_rate=completed / scheduled if scheduled else None,
        mean_review_stars=float(mean) if mean is not None else None,
        review_count=reviews,
        caveat="Cumulative demo counters include seeded records and are not experimental findings. Ratings summarize recorded feedback, not measured user satisfaction.",
    )

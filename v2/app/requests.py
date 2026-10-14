from fastapi import APIRouter, Query
from sqlalchemy import or_, select

from app.errors import require
from app.matching import save_match_run
from app.models import ExchangeRequest, MatchCandidate, MatchRun, Notification, Skill, now
from app.schemas import MatchOut, MatchResults, Page, RequestInput, RequestOut, Selection
from app.security import CurrentUser, Db

router = APIRouter(tags=["Requests and matching"])


def load_request(db, request_id, user_id, lock=False, learner_only=False):
    statement = select(ExchangeRequest).where(ExchangeRequest.id == request_id)
    if lock:
        statement = statement.with_for_update().execution_options(populate_existing=True)
    item = db.scalar(statement)
    require(item is not None, "REQUEST_NOT_FOUND", "Request does not exist", 404)
    permitted = item.learner_id == user_id or (not learner_only and item.provider_id == user_id)
    require(permitted, "REQUEST_FORBIDDEN", "You cannot access this request", 403)
    return item


@router.post("/requests", response_model=RequestOut, status_code=201)
def create_request(payload: RequestInput, db: Db, user: CurrentUser):
    require(
        db.get(Skill, payload.skill_id) is not None, "SKILL_NOT_FOUND", "Skill does not exist", 404
    )
    require(
        payload.window_start > now(), "PAST_REQUEST", "Request window must start in the future", 422
    )
    item = ExchangeRequest(learner_id=user.id, **payload.model_dump())
    db.add(item)
    db.commit()
    return item


@router.get("/requests", response_model=Page[RequestOut])
def list_requests(
    db: Db,
    user: CurrentUser,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    items = db.scalars(
        select(ExchangeRequest)
        .where(or_(ExchangeRequest.learner_id == user.id, ExchangeRequest.provider_id == user.id))
        .order_by(ExchangeRequest.created_at.desc(), ExchangeRequest.id)
        .limit(limit)
        .offset(offset)
    ).all()
    return Page(items=items, limit=limit, offset=offset)


@router.get("/requests/{request_id}", response_model=RequestOut)
def get_request(request_id: str, db: Db, user: CurrentUser):
    return load_request(db, request_id, user.id)


@router.post("/requests/{request_id}/matches", response_model=MatchResults)
def matches(request_id: str, db: Db, user: CurrentUser):
    item = load_request(db, request_id, user.id, lock=True, learner_only=True)
    require(item.status == "OPEN", "REQUEST_NOT_OPEN", "Only open requests can be matched")
    run, candidates = save_match_run(db, item)
    db.commit()
    return MatchResults(
        run_id=run.id,
        algorithm=run.algorithm,
        weights=run.weights,
        candidates=[MatchOut.model_validate(c) for c in candidates],
    )


@router.post("/requests/{request_id}/select", response_model=RequestOut)
def select_provider(request_id: str, payload: Selection, db: Db, user: CurrentUser):
    item = load_request(db, request_id, user.id, lock=True, learner_only=True)
    require(item.status == "OPEN", "REQUEST_NOT_OPEN", "Only open requests can select a provider")
    candidate = db.get(MatchCandidate, payload.candidate_id)
    run = db.get(MatchRun, candidate.run_id) if candidate else None
    require(
        run is not None and run.request_id == item.id and run.algorithm == "full-v1",
        "INVALID_CANDIDATE",
        "Select a candidate from this request's full matching results",
        422,
    )
    require(
        candidate.suggested_start > now(),
        "MATCH_EXPIRED",
        "The suggested slot has passed; run matching again",
    )
    item.provider_id = candidate.provider_id
    item.offered_skill_id = candidate.offered_skill_id
    item.selected_start = candidate.suggested_start
    item.status = "REQUESTED"
    db.add(
        Notification(
            user_id=item.provider_id,
            content="A learner requested a skill session",
            resource_id=item.id,
        )
    )
    db.commit()
    return item


@router.post("/requests/{request_id}/reject", response_model=RequestOut)
def reject(request_id: str, db: Db, user: CurrentUser):
    item = load_request(db, request_id, user.id, lock=True)
    require(
        item.provider_id == user.id,
        "PROVIDER_REQUIRED",
        "Only the selected provider can reject",
        403,
    )
    if item.status == "REJECTED":
        return item
    require(
        item.status == "REQUESTED", "INVALID_REQUEST_STATE", "Request is not awaiting a response"
    )
    item.status = "REJECTED"
    db.add(
        Notification(
            user_id=item.learner_id,
            content="Your session request was rejected",
            resource_id=item.id,
        )
    )
    db.commit()
    return item


@router.post("/requests/{request_id}/cancel", response_model=RequestOut)
def cancel(request_id: str, db: Db, user: CurrentUser):
    item = load_request(db, request_id, user.id, lock=True, learner_only=True)
    if item.status == "CANCELLED":
        return item
    require(
        item.status in {"OPEN", "REQUESTED"},
        "INVALID_REQUEST_STATE",
        "Cancel an accepted request through its session",
    )
    item.status = "CANCELLED"
    if item.provider_id:
        db.add(
            Notification(
                user_id=item.provider_id,
                content="A session request was cancelled",
                resource_id=item.id,
            )
        )
    db.commit()
    return item

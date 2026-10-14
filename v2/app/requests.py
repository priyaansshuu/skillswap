import hashlib
import json
from typing import Literal

from fastapi import APIRouter, Header, Query
from sqlalchemy import or_, select, text

from app.accounting import lock_users, wallet
from app.discovery import provider_profiles
from app.errors import require
from app.matching import rank_candidates, save_match_run
from app.models import (
    ExchangeRequest,
    MatchCandidate,
    MatchRun,
    Notification,
    RequestSubmission,
    Skill,
    User,
    now,
)
from app.schemas import (
    MatchOut,
    MatchResults,
    Page,
    PreviewCandidate,
    RequestInput,
    RequestOut,
    RequestPreview,
    Selection,
)
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


def request_draft(payload, db, user):
    require(
        db.get(Skill, payload.skill_id) is not None, "SKILL_NOT_FOUND", "Skill does not exist", 404
    )
    require(
        payload.window_start > now(), "PAST_REQUEST", "Request window must start in the future", 422
    )
    return ExchangeRequest(learner_id=user.id, **payload.model_dump())


@router.post("/requests/preview", response_model=RequestPreview)
def preview_request(payload: RequestInput, db: Db, user: CurrentUser):
    draft = request_draft(payload, db, user)
    candidates, _ = rank_candidates(db, draft)
    if payload.provider_id:
        candidates = [c for c in candidates if c["provider_id"] == payload.provider_id]
    available = wallet(db, user.id).available_minutes
    eligible = bool(candidates) and available >= payload.duration_minutes
    reason = None
    if available < payload.duration_minutes:
        reason = "You do not have enough available minutes for this duration."
    elif not candidates:
        reason = "No eligible member has a free slot in this window. Try another time or member."
    candidates = candidates[:50]
    ids = [c["provider_id"] for c in candidates]
    profiles = {
        p.id: p
        for p in provider_profiles(db, db.scalars(select(User).where(User.id.in_(ids))).all())
    }
    return RequestPreview(
        eligible=eligible,
        reason=reason,
        available_minutes=available,
        candidates=[
            PreviewCandidate(
                provider=profiles[c["provider_id"]],
                **{
                    k: c[k]
                    for k in ("offered_skill_id", "suggested_start", "score", "hierarchy_distance")
                },
            )
            for c in candidates
        ],
    )


@router.post("/requests", response_model=RequestOut, status_code=201)
def create_request(
    payload: RequestInput,
    db: Db,
    user: CurrentUser,
    idempotency_key: str | None = Header(
        default=None, min_length=8, max_length=128, pattern=r"^[A-Za-z0-9._:-]+$"
    ),
):
    fingerprint = hashlib.sha256(
        json.dumps(payload.model_dump(mode="json"), sort_keys=True).encode()
    ).hexdigest()
    if idempotency_key:
        # Serialize only retries by this account/key, across workers and connections.
        lock_id = int.from_bytes(
            hashlib.sha256((user.id + ":" + idempotency_key).encode()).digest()[:8],
            "big",
            signed=True,
        )
        db.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": lock_id})
        previous = db.get(RequestSubmission, (user.id, idempotency_key))
        if previous:
            require(
                previous.payload_hash == fingerprint,
                "IDEMPOTENCY_CONFLICT",
                "This submission key was already used for different request details",
            )
            return db.get(ExchangeRequest, previous.request_id)
    item = request_draft(payload, db, user)
    if payload.provider_id:
        lock_users(db, user.id, payload.provider_id)
        require(
            wallet(db, user.id).available_minutes >= payload.duration_minutes,
            "INSUFFICIENT_CREDITS",
            "You do not have enough available time credits",
        )
        candidates, _ = rank_candidates(db, item)
        candidate = next((c for c in candidates if c["provider_id"] == payload.provider_id), None)
        require(
            candidate is not None,
            "SLOT_UNAVAILABLE",
            "This member has no eligible free slot. Preview another time before requesting.",
        )
        item.offered_skill_id = candidate["offered_skill_id"]
        item.selected_start = candidate["suggested_start"]
        item.status = "REQUESTED"
    db.add(item)
    db.flush()
    if payload.provider_id:
        db.add(
            Notification(
                user_id=payload.provider_id,
                content="A learner requested a skill session",
                resource_id=item.id,
            )
        )
    if idempotency_key:
        db.add(
            RequestSubmission(
                user_id=user.id, key=idempotency_key, payload_hash=fingerprint, request_id=item.id
            )
        )
    db.commit()
    return item


@router.get("/requests", response_model=Page[RequestOut])
def list_requests(
    db: Db,
    user: CurrentUser,
    role: Literal["all", "teaching", "learning"] = "all",
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    ownership = (
        ExchangeRequest.provider_id == user.id
        if role == "teaching"
        else ExchangeRequest.learner_id == user.id
        if role == "learning"
        else or_(ExchangeRequest.learner_id == user.id, ExchangeRequest.provider_id == user.id)
    )
    items = db.scalars(
        select(ExchangeRequest)
        .where(ownership)
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

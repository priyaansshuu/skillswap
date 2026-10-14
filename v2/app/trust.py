from fastapi import APIRouter, Query
from sqlalchemy import select

from app.accounting import lock_users, wallet
from app.catalog import public_user
from app.config import get_settings
from app.errors import require
from app.models import (
    AuditRecord,
    CreditEntry,
    Dispute,
    ExchangeRequest,
    Notification,
    Review,
    User,
    now,
)
from app.reputation import add_event, reputations
from app.schemas import (
    AuditOut,
    DisputeInput,
    DisputeOut,
    ModerateInput,
    NotificationOut,
    Page,
    PublicProfile,
    ReputationOut,
    ResolveInput,
    ReviewInput,
    ReviewOut,
    SessionOut,
)
from app.security import AdminUser, CurrentUser, Db
from app.sessions import load_session, notify, release_session

router = APIRouter(tags=["Reviews, reputation and notifications"])
admin_router = APIRouter(prefix="/admin", tags=["Administration"])


@router.post("/sessions/{session_id}/reviews", response_model=ReviewOut, status_code=201)
def review_session(session_id: str, payload: ReviewInput, db: Db, user: CurrentUser):
    session = load_session(db, session_id, user.id, lock=True)
    require(
        session.status == "COMPLETED",
        "SESSION_NOT_COMPLETED",
        "Only completed sessions can be reviewed",
    )
    require(
        not db.scalar(
            select(Review.id).where(Review.session_id == session.id, Review.reviewer_id == user.id)
        ),
        "REVIEW_EXISTS",
        "You already reviewed this session",
    )
    target = session.provider_id if user.id == session.learner_id else session.learner_id
    item = Review(
        session_id=session.id, reviewer_id=user.id, reviewee_id=target, **payload.model_dump()
    )
    db.add(item)
    db.flush()
    add_event(
        db,
        target,
        session.skill_id if target == session.provider_id else None,
        session.id,
        "review:" + item.id,
        "REVIEW",
        (payload.stars - 3) * 5,
    )
    db.add(
        Notification(
            user_id=target,
            content="Your completed session received a review",
            resource_id=session.id,
        )
    )
    db.commit()
    return item


@router.get("/sessions/{session_id}/reviews", response_model=list[ReviewOut])
def session_reviews(session_id: str, db: Db, user: CurrentUser):
    load_session(db, session_id, user.id)
    return db.scalars(
        select(Review).where(Review.session_id == session_id).order_by(Review.created_at, Review.id)
    ).all()


@router.get("/users/{user_id}/reputation", response_model=ReputationOut)
def reputation(user_id: str, db: Db, user: CurrentUser, skill_id: str | None = None):
    public_user(db, user_id, user.id)
    as_of = now()
    score, count = reputations(db, [user_id], skill_id, as_of)[user_id]
    return ReputationOut(
        user_id=user_id,
        skill_id=skill_id,
        score=round(score, 6),
        event_count=count,
        half_life_days=get_settings().reputation_half_life_days,
        as_of=as_of,
    )


@router.get("/notifications", response_model=Page[NotificationOut])
def notifications(
    db: Db,
    user: CurrentUser,
    unread_only: bool = False,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    statement = select(Notification).where(Notification.user_id == user.id)
    if unread_only:
        statement = statement.where(Notification.is_read.is_(False))
    items = db.scalars(
        statement.order_by(Notification.created_at.desc(), Notification.id)
        .limit(limit)
        .offset(offset)
    ).all()
    return Page(items=items, limit=limit, offset=offset)


@router.post("/notifications/{notification_id}/read", response_model=NotificationOut)
def read_notification(notification_id: str, db: Db, user: CurrentUser):
    item = db.get(Notification, notification_id)
    require(
        item is not None and item.user_id == user.id,
        "NOTIFICATION_NOT_FOUND",
        "Notification does not exist",
        404,
    )
    item.is_read = True
    db.commit()
    return item


@router.post("/sessions/{session_id}/disputes", response_model=DisputeOut, status_code=201)
def open_dispute(session_id: str, payload: DisputeInput, db: Db, user: CurrentUser):
    session = load_session(db, session_id, user.id, lock=True)
    require(
        session.status in {"SCHEDULED", "IN_PROGRESS", "COMPLETED", "CANCELLED"},
        "INVALID_DISPUTE_STATE",
        "Session cannot be disputed",
    )
    require(
        not db.scalar(select(Dispute.id).where(Dispute.session_id == session.id)),
        "DISPUTE_EXISTS",
        "This session already has a dispute",
    )
    item = Dispute(
        session_id=session.id,
        reporter_id=user.id,
        reason=payload.reason,
        previous_status=session.status,
    )
    db.add(item)
    session.status = "DISPUTED"
    notify(db, session, "A session dispute was opened; completion is paused pending resolution")
    db.commit()
    return item


@router.get("/sessions/{session_id}/dispute", response_model=DisputeOut)
def get_dispute(session_id: str, db: Db, user: CurrentUser):
    load_session(db, session_id, user.id)
    item = db.scalar(select(Dispute).where(Dispute.session_id == session_id))
    require(item is not None, "DISPUTE_NOT_FOUND", "Session has no dispute", 404)
    return item


@admin_router.get("/disputes", response_model=Page[DisputeOut])
def admin_disputes(
    db: Db,
    admin: AdminUser,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    return Page(
        items=db.scalars(
            select(Dispute)
            .order_by(Dispute.created_at.desc(), Dispute.id)
            .limit(limit)
            .offset(offset)
        ).all(),
        limit=limit,
        offset=offset,
    )


@admin_router.get("/sessions/{session_id}", response_model=SessionOut)
def admin_session(session_id: str, db: Db, admin: AdminUser):
    return load_session(db, session_id, admin.id, admin=True)


@admin_router.post("/disputes/{dispute_id}/resolve", response_model=DisputeOut)
def resolve_dispute(dispute_id: str, payload: ResolveInput, db: Db, admin: AdminUser):
    item = db.get(Dispute, dispute_id)
    require(item is not None, "DISPUTE_NOT_FOUND", "Dispute does not exist", 404)
    session = load_session(db, item.session_id, admin.id, lock=True, admin=True)
    item = db.scalar(
        select(Dispute)
        .where(Dispute.id == dispute_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if item.status == "RESOLVED":
        audit = db.scalar(
            select(AuditRecord).where(
                AuditRecord.action == "RESOLVE_DISPUTE", AuditRecord.resource_id == item.id
            )
        )
        require(
            audit is not None and audit.details == payload.model_dump(),
            "ALREADY_RESOLVED",
            "Dispute was resolved with a different decision",
        )
        return item
    require(
        session.status == "DISPUTED",
        "INVALID_DISPUTE_STATE",
        "Session is not awaiting dispute resolution",
    )
    if payload.action == "DISMISS":
        session.status = item.previous_status
    elif payload.action == "CANCEL":
        require(
            item.previous_status in {"SCHEDULED", "IN_PROGRESS", "CANCELLED"},
            "ALREADY_SETTLED",
            "Use a linked reversal for a completed session",
        )
        if item.previous_status == "CANCELLED":
            session.status = "CANCELLED"
        else:
            release_session(db, session)
    elif payload.action == "REVERSE":
        require(
            item.previous_status == "COMPLETED",
            "NOT_SETTLED",
            "Only completed exchanges can be reversed",
        )
        transfer = db.scalar(
            select(CreditEntry).where(
                CreditEntry.session_id == session.id, CreditEntry.kind == "TRANSFER"
            )
        )
        require(transfer is not None, "MISSING_TRANSFER", "Session has no recorded transfer")
        require(
            wallet(db, session.provider_id).available_minutes >= transfer.minutes,
            "REVERSAL_INSUFFICIENT_CREDITS",
            "Provider lacks unreserved credits; the dispute remains open",
        )
        session.status = "REVERSED"
        db.get(ExchangeRequest, session.request_id).status = "CANCELLED"
        db.flush()
        db.add(
            CreditEntry(
                sender_id=session.provider_id,
                receiver_id=session.learner_id,
                session_id=session.id,
                kind="REVERSAL",
                reversal_of=transfer.id,
                minutes=transfer.minutes,
            )
        )
    if payload.penalty != "NONE":
        require(
            payload.responsible_user_id in {session.learner_id, session.provider_id},
            "INVALID_PENALTY_TARGET",
            "Only a participant can receive this penalty",
            422,
        )
        delta = -10 if payload.penalty == "NO_SHOW" else -5
        target = payload.responsible_user_id
        add_event(
            db,
            target,
            session.skill_id if target == session.provider_id else None,
            session.id,
            "dispute:" + item.id,
            payload.penalty,
            delta,
        )
    item.status = "RESOLVED"
    item.resolution = payload.note
    db.add(
        AuditRecord(
            admin_id=admin.id,
            action="RESOLVE_DISPUTE",
            resource_id=item.id,
            details=payload.model_dump(),
        )
    )
    notify(db, session, "An administrator resolved your session dispute")
    db.commit()
    return item


@admin_router.post("/users/{user_id}/moderate", response_model=PublicProfile)
def moderate_user(user_id: str, payload: ModerateInput, db: Db, admin: AdminUser):
    lock_users(db, user_id)
    target = db.get(User, user_id)
    require(target is not None, "USER_NOT_FOUND", "User does not exist", 404)
    require(
        not target.is_admin,
        "ADMIN_MODERATION",
        "Administrator accounts must be managed through the local CLI",
    )
    target.active = payload.active
    db.add(
        AuditRecord(
            admin_id=admin.id,
            action="MODERATE_USER",
            resource_id=user_id,
            details=payload.model_dump(),
        )
    )
    db.commit()
    return target


@admin_router.get("/audit", response_model=Page[AuditOut])
def audit_records(
    db: Db,
    admin: AdminUser,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    items = db.scalars(
        select(AuditRecord)
        .order_by(AuditRecord.created_at.desc(), AuditRecord.id)
        .limit(limit)
        .offset(offset)
    ).all()
    return Page(items=items, limit=limit, offset=offset)

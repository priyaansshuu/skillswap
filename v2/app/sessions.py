from datetime import timedelta

from fastapi import APIRouter, Query
from sqlalchemy import or_, select

from app.accounting import lock_users, wallet
from app.errors import require
from app.matching import selected_slot_valid
from app.models import (
    Confirmation,
    CreditEntry,
    ExchangeRequest,
    ExchangeSession,
    Notification,
    Reservation,
    User,
    now,
)
from app.reputation import add_event
from app.requests import load_request
from app.schemas import ConfirmationOut, ConfirmInput, CreditOut, Page, SessionOut, Wallet
from app.security import CurrentUser, Db

router = APIRouter(tags=["Sessions and wallet"])


def notify(db, session, message):
    for user_id in (session.learner_id, session.provider_id):
        db.add(Notification(user_id=user_id, content=message, resource_id=session.id))


def load_session(db, session_id, actor_id, lock=False, admin=False):
    item = db.get(ExchangeSession, session_id)
    require(item is not None, "SESSION_NOT_FOUND", "Session does not exist", 404)
    require(
        admin or actor_id in (item.learner_id, item.provider_id),
        "SESSION_FORBIDDEN",
        "You cannot access this session",
        403,
    )
    if lock:
        lock_users(db, item.learner_id, item.provider_id)
        db.scalar(
            select(ExchangeRequest).where(ExchangeRequest.id == item.request_id).with_for_update()
        )
        item = db.scalar(
            select(ExchangeSession)
            .where(ExchangeSession.id == session_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
    return item


@router.post("/requests/{request_id}/accept", response_model=SessionOut)
def accept(request_id: str, db: Db, user: CurrentUser):
    item = load_request(db, request_id, user.id)
    require(
        item.provider_id == user.id,
        "PROVIDER_REQUIRED",
        "Only the selected provider can accept",
        403,
    )
    lock_users(db, item.learner_id, item.provider_id)
    item = load_request(db, request_id, user.id, lock=True)
    if item.status in {"ACCEPTED", "FULFILLED"}:
        return db.scalar(select(ExchangeSession).where(ExchangeSession.request_id == item.id))
    require(
        item.status == "REQUESTED", "INVALID_REQUEST_STATE", "Request is not awaiting acceptance"
    )
    require(db.get(User, item.learner_id).active, "INACTIVE_LEARNER", "Learner is unavailable")
    require(item.selected_start > now(), "MATCH_EXPIRED", "The selected slot has passed")
    require(
        selected_slot_valid(db, item), "SLOT_UNAVAILABLE", "Provider or slot is no longer available"
    )
    require(
        wallet(db, item.learner_id).available_minutes >= item.duration_minutes,
        "INSUFFICIENT_CREDITS",
        "Learner does not have enough available time credits",
    )
    session = ExchangeSession(
        request_id=item.id,
        learner_id=item.learner_id,
        provider_id=item.provider_id,
        skill_id=item.offered_skill_id,
        starts_at=item.selected_start,
        ends_at=item.selected_start + timedelta(minutes=item.duration_minutes),
    )
    db.add(session)
    db.flush()
    db.add(
        Reservation(session_id=session.id, user_id=item.learner_id, minutes=item.duration_minutes)
    )
    item.status = "ACCEPTED"
    notify(db, session, "Your skill session is scheduled")
    db.commit()
    return session


@router.get("/sessions", response_model=Page[SessionOut])
def sessions(
    db: Db,
    user: CurrentUser,
    upcoming: bool = False,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    statement = select(ExchangeSession).where(
        or_(ExchangeSession.learner_id == user.id, ExchangeSession.provider_id == user.id)
    )
    if upcoming:
        statement = statement.where(
            ExchangeSession.status.in_(["SCHEDULED", "IN_PROGRESS"]),
            ExchangeSession.ends_at > now(),
        )
    items = db.scalars(
        statement.order_by(
            ExchangeSession.starts_at if upcoming else ExchangeSession.starts_at.desc(),
            ExchangeSession.id,
        )
        .limit(limit)
        .offset(offset)
    ).all()
    return Page(items=items, limit=limit, offset=offset)


@router.get("/sessions/{session_id}", response_model=SessionOut)
def get_session(session_id: str, db: Db, user: CurrentUser):
    return load_session(db, session_id, user.id)


@router.get("/sessions/{session_id}/confirmations", response_model=list[ConfirmationOut])
def confirmations(session_id: str, db: Db, user: CurrentUser):
    load_session(db, session_id, user.id)
    return db.scalars(
        select(Confirmation)
        .where(Confirmation.session_id == session_id)
        .order_by(Confirmation.user_id)
    ).all()


@router.post("/sessions/{session_id}/start", response_model=SessionOut)
def start(session_id: str, db: Db, user: CurrentUser):
    session = load_session(db, session_id, user.id, lock=True)
    if session.status == "IN_PROGRESS":
        return session
    require(session.status == "SCHEDULED", "INVALID_SESSION_STATE", "Session cannot be started")
    require(now() >= session.starts_at, "TOO_EARLY", "Session has not reached its scheduled start")
    session.status = "IN_PROGRESS"
    notify(db, session, "Your skill session has started")
    db.commit()
    return session


def release_session(db, session):
    reservation = db.get(Reservation, session.id)
    require(
        reservation is not None and reservation.status == "HELD",
        "INVALID_RESERVATION",
        "Session has no active reservation",
    )
    reservation.status = "RELEASED"
    session.status = "CANCELLED"
    db.get(ExchangeRequest, session.request_id).status = "CANCELLED"
    notify(db, session, "Your skill session was cancelled; held credits were released")


@router.post("/sessions/{session_id}/cancel", response_model=SessionOut)
def cancel_session(session_id: str, db: Db, user: CurrentUser):
    session = load_session(db, session_id, user.id, lock=True)
    if session.status == "CANCELLED":
        return session
    require(
        session.status == "SCHEDULED" and now() < session.starts_at,
        "CANNOT_CANCEL",
        "After the scheduled start, open a dispute for administrator resolution",
    )
    release_session(db, session)
    db.commit()
    return session


def settle_session(db, session, minutes):
    reservation = db.get(Reservation, session.id)
    require(
        reservation is not None and reservation.status == "HELD",
        "INVALID_RESERVATION",
        "Session has no active reservation",
    )
    require(
        minutes <= reservation.minutes,
        "DURATION_EXCEEDS_RESERVATION",
        "Duration exceeds reserved credits",
        422,
    )
    require(
        wallet(db, session.learner_id).balance_minutes >= minutes,
        "INSUFFICIENT_CREDITS",
        "Learner balance cannot cover settlement",
    )
    session.actual_minutes = minutes
    session.completed_at = now()
    session.status = "COMPLETED"
    reservation.status = "CONSUMED"
    db.get(ExchangeRequest, session.request_id).status = "FULFILLED"
    db.flush()
    db.add(
        CreditEntry(
            sender_id=session.learner_id,
            receiver_id=session.provider_id,
            session_id=session.id,
            kind="TRANSFER",
            minutes=minutes,
        )
    )
    add_event(
        db,
        session.provider_id,
        session.skill_id,
        session.id,
        "completion:" + session.id,
        "COMPLETION",
        2,
    )
    db.flush()
    notify(db, session, "Both participants confirmed completion; time credits were transferred")


@router.post("/sessions/{session_id}/confirm", response_model=SessionOut)
def confirm(session_id: str, payload: ConfirmInput, db: Db, user: CurrentUser):
    session = load_session(db, session_id, user.id, lock=True)
    if session.status == "COMPLETED":
        require(
            session.actual_minutes == payload.minutes,
            "ALREADY_SETTLED",
            "Completed duration cannot be changed",
        )
        return session
    require(
        session.status == "IN_PROGRESS",
        "INVALID_SESSION_STATE",
        "Start the session before confirming it; disputed sessions require resolution",
    )
    require(now() >= session.ends_at, "TOO_EARLY", "Wait until the scheduled session end")
    reservation = db.get(Reservation, session.id)
    require(
        payload.minutes <= reservation.minutes,
        "DURATION_EXCEEDS_RESERVATION",
        "Duration exceeds reserved credits",
        422,
    )
    existing = db.get(Confirmation, (session.id, user.id))
    if existing:
        existing.minutes = payload.minutes
    else:
        db.add(Confirmation(session_id=session.id, user_id=user.id, minutes=payload.minutes))
    db.flush()
    confirmations = db.scalars(
        select(Confirmation).where(Confirmation.session_id == session.id)
    ).all()
    if len(confirmations) == 2 and len({c.minutes for c in confirmations}) == 1:
        settle_session(db, session, payload.minutes)
    db.commit()
    return session


@router.get("/me/wallet", response_model=Wallet)
def my_wallet(db: Db, user: CurrentUser):
    return wallet(db, user.id)


@router.get("/me/credits", response_model=Page[CreditOut])
def credits(
    db: Db,
    user: CurrentUser,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    items = db.scalars(
        select(CreditEntry)
        .where(or_(CreditEntry.sender_id == user.id, CreditEntry.receiver_id == user.id))
        .order_by(CreditEntry.created_at.desc(), CreditEntry.id)
        .limit(limit)
        .offset(offset)
    ).all()
    return Page(items=items, limit=limit, offset=offset)

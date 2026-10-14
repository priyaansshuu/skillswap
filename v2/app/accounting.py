from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import CreditEntry, ExchangeSession, Reservation, User
from app.schemas import Wallet


def lock_users(db: Session, *ids: str):
    # Every balance/schedule writer shares this lock order.
    return db.scalars(
        select(User)
        .where(User.id.in_(set(ids)))
        .order_by(User.id)
        .with_for_update()
        .execution_options(populate_existing=True)
    ).all()


def wallet(db: Session, user_id: str):
    incoming = db.scalar(
        select(func.coalesce(func.sum(CreditEntry.minutes), 0)).where(
            CreditEntry.receiver_id == user_id
        )
    )
    outgoing = db.scalar(
        select(func.coalesce(func.sum(CreditEntry.minutes), 0)).where(
            CreditEntry.sender_id == user_id
        )
    )
    reserved = db.scalar(
        select(func.coalesce(func.sum(Reservation.minutes), 0)).where(
            Reservation.user_id == user_id, Reservation.status == "HELD"
        )
    )
    taught = db.scalar(
        select(func.coalesce(func.sum(ExchangeSession.actual_minutes), 0)).where(
            ExchangeSession.provider_id == user_id,
            ExchangeSession.status.in_(["COMPLETED", "DISPUTED"]),
        )
    )
    balance = int(incoming - outgoing)
    return Wallet(
        balance_minutes=balance,
        reserved_minutes=int(reserved),
        available_minutes=balance - int(reserved),
        taught_minutes=int(taught),
    )

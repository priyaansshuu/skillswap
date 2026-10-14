from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def now():
    return datetime.now(timezone.utc)


def new_id():
    return str(uuid4())


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(254), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    city: Mapped[str | None] = mapped_column(String(100))
    campus: Mapped[str | None] = mapped_column(String(100))
    bio: Mapped[str] = mapped_column(String(1000), default="")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Skill(Base):
    __tablename__ = "skills"
    __table_args__ = (
        CheckConstraint("parent_id IS NULL OR parent_id <> id", name="skill_not_own_parent"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    category: Mapped[str] = mapped_column(String(100))
    parent_id: Mapped[str | None] = mapped_column(ForeignKey("skills.id"))


class UserSkill(Base):
    __tablename__ = "user_skills"
    __table_args__ = (
        CheckConstraint("kind IN ('OFFER','WANT')", name="valid_skill_kind"),
        CheckConstraint("level BETWEEN 1 AND 5", name="valid_skill_level"),
        Index("ix_user_skills_lookup", "skill_id", "kind"),
    )
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    skill_id: Mapped[str] = mapped_column(ForeignKey("skills.id"), primary_key=True)
    kind: Mapped[str] = mapped_column(String(5), primary_key=True)
    level: Mapped[int] = mapped_column(Integer)


class Availability(Base):
    __tablename__ = "availability"
    __table_args__ = (
        CheckConstraint("ends_at > starts_at", name="positive_availability"),
        Index("ix_availability_user_time", "user_id", "starts_at", "ends_at"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    mode: Mapped[str] = mapped_column(String(10))
    __table_args__ += (CheckConstraint("mode IN ('ONLINE','IN_PERSON')", name="availability_mode"),)


class Block(Base):
    __tablename__ = "blocks"
    __table_args__ = (CheckConstraint("user_id <> blocked_id", name="cannot_block_self"),)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    blocked_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)


class ExchangeRequest(Base):
    __tablename__ = "requests"
    __table_args__ = (
        CheckConstraint("duration_minutes BETWEEN 1 AND 480", name="request_duration"),
        CheckConstraint("window_end > window_start", name="request_window"),
        CheckConstraint(
            "provider_id IS NULL OR provider_id <> learner_id", name="request_not_self"
        ),
        CheckConstraint(
            "status IN ('OPEN','REQUESTED','ACCEPTED','REJECTED','CANCELLED','FULFILLED')",
            name="request_status",
        ),
        CheckConstraint("mode IN ('ONLINE','IN_PERSON')", name="request_mode"),
        Index("ix_requests_learner_created", "learner_id", "created_at"),
        Index("ix_requests_provider_created", "provider_id", "created_at"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    learner_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    provider_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    skill_id: Mapped[str] = mapped_column(ForeignKey("skills.id"))
    offered_skill_id: Mapped[str | None] = mapped_column(ForeignKey("skills.id"))
    duration_minutes: Mapped[int] = mapped_column(Integer)
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    window_end: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    selected_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    mode: Mapped[str] = mapped_column(String(10))
    status: Mapped[str] = mapped_column(String(12), default="OPEN")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class MatchRun(Base):
    __tablename__ = "match_runs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    request_id: Mapped[str] = mapped_column(ForeignKey("requests.id"), index=True)
    algorithm: Mapped[str] = mapped_column(String(30))
    weights: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class MatchCandidate(Base):
    __tablename__ = "match_candidates"
    __table_args__ = (UniqueConstraint("run_id", "provider_id", name="unique_run_provider"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    run_id: Mapped[str] = mapped_column(ForeignKey("match_runs.id"))
    provider_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    offered_skill_id: Mapped[str] = mapped_column(ForeignKey("skills.id"))
    score: Mapped[float]
    factors: Mapped[dict] = mapped_column(JSON)
    suggested_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    hierarchy_distance: Mapped[int] = mapped_column(Integer)


class ExchangeSession(Base):
    __tablename__ = "sessions"
    __table_args__ = (
        CheckConstraint("learner_id <> provider_id", name="session_not_self"),
        CheckConstraint("ends_at > starts_at", name="session_interval"),
        CheckConstraint(
            "actual_minutes IS NULL OR actual_minutes BETWEEN 1 AND 480", name="session_actual"
        ),
        CheckConstraint(
            "status IN ('SCHEDULED','IN_PROGRESS','COMPLETED','CANCELLED','DISPUTED','REVERSED')",
            name="session_status",
        ),
        Index("ix_sessions_learner_time", "learner_id", "starts_at", "ends_at"),
        Index("ix_sessions_provider_time", "provider_id", "starts_at", "ends_at"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    request_id: Mapped[str] = mapped_column(ForeignKey("requests.id"), unique=True)
    learner_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    provider_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    skill_id: Mapped[str] = mapped_column(ForeignKey("skills.id"))
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(12), default="SCHEDULED")
    actual_minutes: Mapped[int | None] = mapped_column(Integer)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Reservation(Base):
    __tablename__ = "reservations"
    __table_args__ = (
        CheckConstraint("minutes > 0", name="reservation_positive"),
        CheckConstraint("status IN ('HELD','RELEASED','CONSUMED')", name="reservation_status"),
        Index("ix_reservations_user_status", "user_id", "status"),
    )
    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.id"), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    minutes: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(10), default="HELD")


class CreditEntry(Base):
    __tablename__ = "credit_ledger"
    __table_args__ = (
        CheckConstraint("minutes > 0", name="credit_positive"),
        CheckConstraint("sender_id IS NULL OR sender_id <> receiver_id", name="credit_not_self"),
        CheckConstraint("kind IN ('GRANT','TRANSFER','REVERSAL')", name="credit_kind"),
        CheckConstraint(
            "(kind='GRANT' AND sender_id IS NULL AND session_id IS NULL AND reversal_of IS NULL) OR (kind='TRANSFER' AND sender_id IS NOT NULL AND session_id IS NOT NULL AND reversal_of IS NULL) OR (kind='REVERSAL' AND sender_id IS NOT NULL AND session_id IS NOT NULL AND reversal_of IS NOT NULL)",
            name="credit_shape",
        ),
        Index("ix_credit_receiver", "receiver_id"),
        Index("ix_credit_sender", "sender_id"),
        Index(
            "unique_session_credit_kind",
            "session_id",
            "kind",
            unique=True,
            postgresql_where=text("session_id IS NOT NULL"),
        ),
        Index(
            "unique_starter_grant",
            "receiver_id",
            unique=True,
            postgresql_where=text("kind = 'GRANT'"),
        ),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    sender_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    receiver_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    session_id: Mapped[str | None] = mapped_column(ForeignKey("sessions.id"))
    reversal_of: Mapped[str | None] = mapped_column(ForeignKey("credit_ledger.id"), unique=True)
    kind: Mapped[str] = mapped_column(String(10))
    minutes: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Confirmation(Base):
    __tablename__ = "confirmations"
    __table_args__ = (CheckConstraint("minutes BETWEEN 1 AND 480", name="confirmation_minutes"),)
    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.id"), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    minutes: Mapped[int] = mapped_column(Integer)


class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = (
        CheckConstraint("stars BETWEEN 1 AND 5", name="review_stars"),
        CheckConstraint("reviewer_id <> reviewee_id", name="review_not_self"),
        UniqueConstraint("session_id", "reviewer_id", name="unique_participant_review"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.id"))
    reviewer_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    reviewee_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    stars: Mapped[int] = mapped_column(Integer)
    comment: Mapped[str] = mapped_column(String(2000), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class ReputationEvent(Base):
    __tablename__ = "reputation_events"
    __table_args__ = (
        UniqueConstraint("user_id", "source_key", name="unique_reputation_event"),
        Index("ix_reputation_user_skill_time", "user_id", "skill_id", "created_at"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    skill_id: Mapped[str | None] = mapped_column(ForeignKey("skills.id"))
    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.id"))
    source_key: Mapped[str] = mapped_column(String(100))
    delta: Mapped[int] = mapped_column(Integer)
    kind: Mapped[str] = mapped_column(String(30))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (Index("ix_notifications_user_created", "user_id", "created_at"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    content: Mapped[str] = mapped_column(String(500))
    resource_id: Mapped[str | None] = mapped_column(String(36))
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Dispute(Base):
    __tablename__ = "disputes"
    __table_args__ = (CheckConstraint("status IN ('OPEN','RESOLVED')", name="dispute_status"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.id"), unique=True)
    reporter_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    reason: Mapped[str] = mapped_column(String(2000))
    previous_status: Mapped[str] = mapped_column(String(12))
    status: Mapped[str] = mapped_column(String(10), default="OPEN")
    resolution: Mapped[str | None] = mapped_column(String(2000))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class AuditRecord(Base):
    __tablename__ = "admin_audit"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    admin_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(100))
    resource_id: Mapped[str] = mapped_column(String(36))
    details: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class AuthAttempt(Base):
    __tablename__ = "auth_attempts"
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    bucket: Mapped[int] = mapped_column(Integer, primary_key=True)
    count: Mapped[int] = mapped_column(Integer, default=1)

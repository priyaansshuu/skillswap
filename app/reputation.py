import math
from collections import defaultdict

from sqlalchemy import or_, select

from app.config import get_settings
from app.models import ExchangeSession, ReputationEvent, now


def decayed_score(events, as_of, half_life_days):
    score, previous = 50.0, None
    for event in events:
        if event.created_at > as_of:
            continue
        if previous:
            days = max(0, (event.created_at - previous).total_seconds() / 86400)
            score *= math.exp(-math.log(2) * days / half_life_days)
        score = min(100, max(0, score + event.delta))
        previous = event.created_at
    if previous:
        days = max(0, (as_of - previous).total_seconds() / 86400)
        score *= math.exp(-math.log(2) * days / half_life_days)
    return score


def reputations(db, user_ids, skill_id=None, as_of=None):
    as_of = as_of or now()
    statement = (
        select(ReputationEvent)
        .join(ExchangeSession)
        .where(
            ReputationEvent.user_id.in_(user_ids),
            or_(
                ExchangeSession.status != "REVERSED",
                ReputationEvent.kind.in_(["NO_SHOW", "UNJUSTIFIED_CANCELLATION"]),
            ),
        )
    )
    if skill_id is not None:
        statement = statement.where(ReputationEvent.skill_id == skill_id)
    grouped = defaultdict(list)
    for event in db.scalars(statement.order_by(ReputationEvent.created_at, ReputationEvent.id)):
        grouped[event.user_id].append(event)
    half_life = get_settings().reputation_half_life_days
    return {
        user_id: (decayed_score(grouped[user_id], as_of, half_life), len(grouped[user_id]))
        for user_id in user_ids
    }


def add_event(db, user_id, skill_id, session_id, source_key, kind, delta):
    db.add(
        ReputationEvent(
            user_id=user_id,
            skill_id=skill_id,
            session_id=session_id,
            source_key=source_key,
            kind=kind,
            delta=delta,
        )
    )

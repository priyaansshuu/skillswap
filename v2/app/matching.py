import math
from datetime import timedelta

from sqlalchemy import func, or_, select

from app.config import get_settings
from app.errors import require
from app.models import (
    Availability,
    Block,
    ExchangeSession,
    MatchCandidate,
    MatchRun,
    Skill,
    User,
    UserSkill,
    now,
)
from app.reputation import reputations

ACTIVE_SESSION_STATES = ("SCHEDULED", "IN_PROGRESS", "DISPUTED")
ALGORITHMS = {
    "full-v1": None,
    "exact-v1": {
        "skill": 1.0,
        "reputation": 0.0,
        "activity": 0.0,
        "location": 0.0,
        "availability": 0.0,
    },
    "skill-reputation-v1": {
        "skill": 40 / 65,
        "reputation": 25 / 65,
        "activity": 0.0,
        "location": 0.0,
        "availability": 0.0,
    },
}


def free_intervals(start, end, busy):
    intervals = [(start, end)]
    for busy_start, busy_end in sorted(busy):
        revised = []
        for left, right in intervals:
            if busy_end <= left or busy_start >= right:
                revised.append((left, right))
            else:
                if left < busy_start:
                    revised.append((left, busy_start))
                if busy_end < right:
                    revised.append((busy_end, right))
        intervals = revised
    return intervals


def rank_candidates(db, request, algorithm="full-v1", as_of=None):
    as_of = as_of or now()
    weights = ALGORITHMS[algorithm] or get_settings().match_weights
    learner = db.get(User, request.learner_id)
    blocked_ids = set(db.scalars(select(Block.blocked_id).where(Block.user_id == learner.id)))
    blocked_ids.update(db.scalars(select(Block.user_id).where(Block.blocked_id == learner.id)))
    parent_id, distance, seen = request.skill_id, 0, set()
    while parent_id:
        require(parent_id not in seen, "SKILL_CYCLE", "Skill hierarchy is invalid")
        seen.add(parent_id)
        providers = db.scalars(
            select(User)
            .join(UserSkill)
            .where(
                UserSkill.skill_id == parent_id,
                UserSkill.kind == "OFFER",
                User.active.is_(True),
                User.id != learner.id,
                User.id.not_in(blocked_ids),
            )
            .order_by(User.id)
            .limit(1001)
        ).all()
        require(
            len(providers) <= 1000,
            "SEARCH_TOO_BROAD",
            "This demo supports up to 1,000 providers per skill; narrow the skill",
        )
        ids = [p.id for p in providers]
        slots = db.scalars(
            select(Availability).where(
                Availability.user_id.in_(ids),
                Availability.mode == request.mode,
                Availability.ends_at > request.window_start,
                Availability.starts_at < request.window_end,
            )
        ).all()
        bookings = db.scalars(
            select(ExchangeSession).where(
                or_(
                    ExchangeSession.learner_id.in_([*ids, learner.id]),
                    ExchangeSession.provider_id.in_([*ids, learner.id]),
                ),
                ExchangeSession.status.in_(ACTIVE_SESSION_STATES),
                ExchangeSession.ends_at > request.window_start,
                ExchangeSession.starts_at < request.window_end,
            )
        ).all()
        busy = {user_id: [] for user_id in [*ids, learner.id]}
        for booking in bookings:
            for user_id in (booking.learner_id, booking.provider_id):
                if user_id in busy:
                    busy[user_id].append((booking.starts_at, booking.ends_at))
        provider_slots = {user_id: [] for user_id in ids}
        for slot in slots:
            start = max(slot.starts_at, request.window_start, as_of)
            end = min(slot.ends_at, request.window_end)
            if end > start:
                provider_slots[slot.user_id].extend(
                    free_intervals(start, end, busy[slot.user_id] + busy[learner.id])
                )
        scores = reputations(db, ids, parent_id, as_of)
        latest = dict(
            db.execute(
                select(ExchangeSession.provider_id, func.max(ExchangeSession.completed_at))
                .where(ExchangeSession.provider_id.in_(ids), ExchangeSession.status == "COMPLETED")
                .group_by(ExchangeSession.provider_id)
            ).all()
        )
        candidates = []
        for provider in providers:
            usable = [
                (a, b)
                for a, b in provider_slots[provider.id]
                if (b - a).total_seconds() >= request.duration_minutes * 60
            ]
            if not usable:
                continue
            start = min(a for a, b in usable)
            overlap = max((b - a).total_seconds() for a, b in usable)
            if request.mode == "ONLINE":
                location = 1.0
            elif not learner.city or not provider.city:
                location = 0.5
            else:
                location = float(
                    learner.city.casefold() == provider.city.casefold()
                    and (
                        not learner.campus
                        or not provider.campus
                        or learner.campus.casefold() == provider.campus.casefold()
                    )
                )
            activity = 0.5
            if latest.get(provider.id):
                activity = math.exp(
                    -max(0, (as_of - latest[provider.id]).total_seconds() / 86400) / 30
                )
            factors = {
                "skill": 0.8**distance,
                "reputation": scores[provider.id][0] / 100,
                "activity": activity,
                "location": location,
                "availability": min(
                    1.0, overlap / (request.window_end - request.window_start).total_seconds()
                ),
            }
            candidates.append(
                {
                    "provider_id": provider.id,
                    "offered_skill_id": parent_id,
                    "score": sum(factors[key] * weights[key] for key in weights),
                    "factors": factors,
                    "suggested_start": start,
                    "hierarchy_distance": distance,
                }
            )
        if candidates or algorithm == "exact-v1":
            return sorted(
                candidates, key=lambda item: (-item["score"], item["provider_id"])
            ), weights
        parent_id = db.get(Skill, parent_id).parent_id
        distance += 1
    return [], weights


def save_match_run(db, request, algorithm="full-v1"):
    candidates, weights = rank_candidates(db, request, algorithm)
    run = MatchRun(request_id=request.id, algorithm=algorithm, weights=weights)
    db.add(run)
    db.flush()
    rows = [MatchCandidate(run_id=run.id, **item) for item in candidates[:50]]
    db.add_all(rows)
    db.flush()
    return run, rows


def selected_slot_valid(db, request):
    provider = db.get(User, request.provider_id)
    if not provider or not provider.active:
        return False
    if db.scalar(
        select(Block.user_id).where(
            or_(
                (Block.user_id == request.learner_id) & (Block.blocked_id == request.provider_id),
                (Block.user_id == request.provider_id) & (Block.blocked_id == request.learner_id),
            )
        )
    ):
        return False
    if not db.get(UserSkill, (request.provider_id, request.offered_skill_id, "OFFER")):
        return False
    end = request.selected_start + timedelta(minutes=request.duration_minutes)
    covered = db.scalar(
        select(Availability.id).where(
            Availability.user_id == request.provider_id,
            Availability.mode == request.mode,
            Availability.starts_at <= request.selected_start,
            Availability.ends_at >= end,
        )
    )
    overlap = db.scalar(
        select(ExchangeSession.id).where(
            or_(
                ExchangeSession.learner_id.in_([request.learner_id, request.provider_id]),
                ExchangeSession.provider_id.in_([request.learner_id, request.provider_id]),
            ),
            ExchangeSession.status.in_(ACTIVE_SESSION_STATES),
            ExchangeSession.starts_at < end,
            ExchangeSession.ends_at > request.selected_start,
        )
    )
    return bool(covered) and not overlap

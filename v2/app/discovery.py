"""Sanitized, read-only marketplace discovery; never creates requests."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import func, or_, select

from app.catalog import blocked
from app.errors import require
from app.models import Availability, Block, ExchangeSession, Review, Skill, User, UserSkill, now
from app.reputation import reputations
from app.schemas import Page, ProviderOffer, ProviderProfile, SkillOut
from app.security import Db, current_user

router = APIRouter(prefix="/public", tags=["Public discovery"])
optional_bearer = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token", auto_error=False)


def optional_user(db: Db, token: Annotated[str | None, Depends(optional_bearer)]):
    return current_user(db, token) if token else None


Viewer = Annotated[User | None, Depends(optional_user)]


def provider_profiles(db, users):
    ids = [u.id for u in users]
    offers = {uid: [] for uid in ids}
    for offer, skill in db.execute(
        select(UserSkill, Skill)
        .join(Skill, Skill.id == UserSkill.skill_id)
        .where(UserSkill.user_id.in_(ids), UserSkill.kind == "OFFER")
        .order_by(Skill.name, Skill.id)
    ):
        offers[offer.user_id].append(
            ProviderOffer(
                skill_id=skill.id, name=skill.name, category=skill.category, level=offer.level
            )
        )
    modes = {uid: set() for uid in ids}
    for uid, mode in db.execute(
        select(Availability.user_id, Availability.mode)
        .where(Availability.user_id.in_(ids), Availability.ends_at > now())
        .distinct()
    ):
        modes[uid].add(mode)
    ratings = {
        uid: (count, float(avg))
        for uid, count, avg in db.execute(
            select(Review.reviewee_id, func.count(Review.id), func.avg(Review.stars))
            .join(ExchangeSession, ExchangeSession.id == Review.session_id)
            .where(
                Review.reviewee_id.in_(ids),
                Review.reviewee_id == ExchangeSession.provider_id,
                Review.reviewer_id == ExchangeSession.learner_id,
                ExchangeSession.status == "COMPLETED",
            )
            .group_by(Review.reviewee_id)
        )
    }
    scores = reputations(db, ids)
    return [
        ProviderProfile(
            id=u.id,
            name=u.name,
            city=u.city,
            campus=u.campus,
            bio=u.bio,
            offers=offers[u.id],
            modes=sorted(modes[u.id]),
            rating_count=ratings.get(u.id, (0, None))[0],
            rating_average=ratings.get(u.id, (0, None))[1],
            reputation_score=round(scores[u.id][0], 2),
        )
        for u in users
    ]


@router.get("/skills", response_model=Page[SkillOut])
def public_skills(
    db: Db,
    q: str = Query(default="", max_length=100),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    statement = select(Skill)
    if q:
        statement = statement.where(Skill.name.icontains(q, autoescape=True))
    return Page(
        items=db.scalars(
            statement.order_by(Skill.name, Skill.id).limit(limit).offset(offset)
        ).all(),
        limit=limit,
        offset=offset,
    )


@router.get("/providers", response_model=Page[ProviderProfile])
def providers(
    db: Db,
    viewer: Viewer,
    q: str = Query(default="", max_length=100),
    skill_id: str | None = None,
    category: str | None = Query(default=None, max_length=100),
    city: str = Query(default="", max_length=100),
    campus: str = Query(default="", max_length=100),
    mode: str | None = Query(default=None, pattern="^(ONLINE|IN_PERSON)$"),
    min_level: int = Query(default=1, ge=1, le=5),
    sort: str = Query(default="name", pattern="^(name|name_desc)$"),
    limit: int = Query(default=12, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    offer = (
        select(UserSkill.user_id)
        .join(Skill)
        .where(UserSkill.kind == "OFFER", UserSkill.level >= min_level)
    )
    if skill_id:
        offer = offer.where(Skill.id == skill_id)
    if category:
        offer = offer.where(Skill.category == category)
    if q:
        offer = offer.where(
            or_(
                Skill.name.icontains(q, autoescape=True),
                UserSkill.user_id.in_(
                    select(User.id).where(User.name.icontains(q, autoescape=True))
                ),
            )
        )
    statement = select(User).where(User.active.is_(True), User.id.in_(offer))
    if city:
        statement = statement.where(User.city.icontains(city, autoescape=True))
    if campus:
        statement = statement.where(User.campus.icontains(campus, autoescape=True))
    if mode:
        statement = statement.where(
            User.id.in_(
                select(Availability.user_id).where(
                    Availability.mode == mode, Availability.ends_at > now()
                )
            )
        )
    if viewer:
        excluded = (
            select(Block.blocked_id)
            .where(Block.user_id == viewer.id)
            .union(select(Block.user_id).where(Block.blocked_id == viewer.id))
        )
        statement = statement.where(User.id.not_in(excluded), User.id != viewer.id)
    order = func.lower(User.name).desc() if sort == "name_desc" else func.lower(User.name)
    rows = db.scalars(statement.order_by(order, User.id).limit(limit).offset(offset)).all()
    return Page(items=provider_profiles(db, rows), limit=limit, offset=offset)


@router.get("/providers/{user_id}", response_model=ProviderProfile)
def provider_profile(user_id: str, db: Db, viewer: Viewer):
    user = db.get(User, user_id)
    require(user is not None and user.active, "USER_NOT_FOUND", "Member is unavailable", 404)
    require(
        not viewer or not blocked(db, user_id, viewer.id),
        "USER_NOT_FOUND",
        "Member is unavailable",
        404,
    )
    profiles = provider_profiles(db, [user])
    require(bool(profiles[0].offers), "USER_NOT_FOUND", "Member has no offered skills", 404)
    return profiles[0]

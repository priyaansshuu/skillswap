from fastapi import APIRouter, Query, Response
from sqlalchemy import or_, select, text

from app.accounting import lock_users
from app.errors import fail, require
from app.models import AuditRecord, Availability, Block, Skill, User, UserSkill, now
from app.schemas import (
    AvailabilityInput,
    AvailabilityOut,
    Page,
    PublicProfile,
    SkillInput,
    SkillOut,
    UserSkillInput,
    UserSkillOut,
)
from app.security import AdminUser, CurrentUser, Db

router = APIRouter(tags=["Skills and availability"])


def blocked(db, first, second):
    return (
        db.scalar(
            select(Block.user_id).where(
                or_(
                    (Block.user_id == first) & (Block.blocked_id == second),
                    (Block.user_id == second) & (Block.blocked_id == first),
                )
            )
        )
        is not None
    )


@router.get("/me/blocks", response_model=Page[PublicProfile])
def list_blocks(
    db: Db, user: CurrentUser, limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0)
):
    items = db.scalars(
        select(User)
        .join(Block, Block.blocked_id == User.id)
        .where(Block.user_id == user.id)
        .order_by(User.name, User.id)
        .limit(limit)
        .offset(offset)
    ).all()
    return Page(items=items, limit=limit, offset=offset)


def public_user(db, user_id, viewer_id):
    user = db.get(User, user_id)
    if not user or not user.active or blocked(db, user_id, viewer_id):
        fail(404, "USER_NOT_FOUND", "User is unavailable")
    return user


def validate_parent(db, parent_id, skill_id=None):
    seen = {skill_id} if skill_id else set()
    while parent_id:
        require(parent_id not in seen, "SKILL_CYCLE", "A skill hierarchy cannot contain a cycle")
        seen.add(parent_id)
        parent = db.get(Skill, parent_id)
        require(parent is not None, "PARENT_NOT_FOUND", "Parent skill does not exist", 404)
        parent_id = parent.parent_id


@router.get("/skills", response_model=Page[SkillOut])
def skills(
    db: Db,
    user: CurrentUser,
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


@router.post("/skills", response_model=SkillOut, status_code=201)
def create_skill(payload: SkillInput, db: Db, admin: AdminUser):
    db.execute(text("SELECT pg_advisory_xact_lock(715001)"))
    validate_parent(db, payload.parent_id)
    skill = Skill(**payload.model_dump())
    db.add(skill)
    db.flush()
    db.add(
        AuditRecord(
            admin_id=admin.id,
            action="CREATE_SKILL",
            resource_id=skill.id,
            details=payload.model_dump(),
        )
    )
    db.commit()
    return skill


@router.put("/skills/{skill_id}", response_model=SkillOut)
def update_skill(skill_id: str, payload: SkillInput, db: Db, admin: AdminUser):
    # Serialize hierarchy edits so two concurrent edits cannot introduce a cycle.
    db.execute(text("SELECT pg_advisory_xact_lock(715001)"))
    skill = db.get(Skill, skill_id)
    require(skill is not None, "SKILL_NOT_FOUND", "Skill does not exist", 404)
    validate_parent(db, payload.parent_id, skill_id)
    for field, value in payload.model_dump().items():
        setattr(skill, field, value)
    db.add(
        AuditRecord(
            admin_id=admin.id,
            action="UPDATE_SKILL",
            resource_id=skill.id,
            details=payload.model_dump(),
        )
    )
    db.commit()
    return skill


@router.get("/me/skills", response_model=Page[UserSkillOut])
def my_skills(
    db: Db,
    user: CurrentUser,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    items = db.scalars(
        select(UserSkill)
        .where(UserSkill.user_id == user.id)
        .order_by(UserSkill.skill_id, UserSkill.kind)
        .limit(limit)
        .offset(offset)
    ).all()
    return Page(items=items, limit=limit, offset=offset)


@router.put("/me/skills", response_model=UserSkillOut)
def put_skill(payload: UserSkillInput, db: Db, user: CurrentUser):
    lock_users(db, user.id)
    require(
        db.get(Skill, payload.skill_id) is not None, "SKILL_NOT_FOUND", "Skill does not exist", 404
    )
    key = (user.id, payload.skill_id, payload.kind)
    item = db.get(UserSkill, key)
    if item:
        item.level = payload.level
    else:
        item = UserSkill(user_id=user.id, **payload.model_dump())
        db.add(item)
    db.commit()
    return item


@router.delete("/me/skills/{skill_id}/{kind}", status_code=204)
def remove_skill(skill_id: str, kind: str, db: Db, user: CurrentUser):
    lock_users(db, user.id)
    item = db.get(UserSkill, (user.id, skill_id, kind))
    require(item is not None, "OFFER_NOT_FOUND", "Skill entry does not exist", 404)
    db.delete(item)
    db.commit()
    return Response(status_code=204)


@router.post("/me/availability", response_model=AvailabilityOut, status_code=201)
def create_availability(payload: AvailabilityInput, db: Db, user: CurrentUser):
    require(
        payload.starts_at > now(), "PAST_AVAILABILITY", "Availability must start in the future", 422
    )
    lock_users(db, user.id)
    slot = Availability(user_id=user.id, **payload.model_dump())
    db.add(slot)
    db.commit()
    return slot


@router.get("/me/availability", response_model=Page[AvailabilityOut])
def list_availability(
    db: Db,
    user: CurrentUser,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    items = db.scalars(
        select(Availability)
        .where(Availability.user_id == user.id)
        .order_by(Availability.starts_at, Availability.id)
        .limit(limit)
        .offset(offset)
    ).all()
    return Page(items=items, limit=limit, offset=offset)


@router.delete("/me/availability/{slot_id}", status_code=204)
def delete_availability(slot_id: str, db: Db, user: CurrentUser):
    lock_users(db, user.id)
    slot = db.get(Availability, slot_id)
    require(
        slot is not None and slot.user_id == user.id,
        "SLOT_NOT_FOUND",
        "Availability does not exist",
        404,
    )
    db.delete(slot)
    db.commit()
    return Response(status_code=204)


@router.get("/users/{user_id}", response_model=PublicProfile)
def profile(user_id: str, db: Db, user: CurrentUser):
    return public_user(db, user_id, user.id)


@router.get("/users/{user_id}/skills", response_model=Page[UserSkillOut])
def user_skills(
    user_id: str,
    db: Db,
    user: CurrentUser,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    public_user(db, user_id, user.id)
    items = db.scalars(
        select(UserSkill)
        .where(UserSkill.user_id == user_id)
        .order_by(UserSkill.skill_id, UserSkill.kind)
        .limit(limit)
        .offset(offset)
    ).all()
    return Page(items=items, limit=limit, offset=offset)


@router.put("/me/blocks/{target_id}", status_code=204)
def block(target_id: str, db: Db, user: CurrentUser):
    require(target_id != user.id, "SELF_BLOCK", "You cannot block yourself", 422)
    lock_users(db, user.id, target_id)
    require(db.get(User, target_id) is not None, "USER_NOT_FOUND", "User does not exist", 404)
    if not db.get(Block, (user.id, target_id)):
        db.add(Block(user_id=user.id, blocked_id=target_id))
    db.commit()
    return Response(status_code=204)


@router.delete("/me/blocks/{target_id}", status_code=204)
def unblock(target_id: str, db: Db, user: CurrentUser):
    lock_users(db, user.id, target_id)
    item = db.get(Block, (user.id, target_id))
    if item:
        db.delete(item)
    db.commit()
    return Response(status_code=204)

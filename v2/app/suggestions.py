"""Member suggestions and administrator-only resolution."""

from fastapi import APIRouter, Query
from sqlalchemy import func, or_, select, text

from app.catalog import validate_parent
from app.errors import require
from app.models import AuditRecord, Notification, Skill, SkillSuggestion, User
from app.schemas import AdminMember, Page, SuggestionDecision, SuggestionInput, SuggestionOut
from app.security import AdminUser, CurrentUser, Db

router = APIRouter(tags=["Skill suggestions"])
admin_router = APIRouter(prefix="/admin", tags=["Administration"])


@router.post("/skill-suggestions", response_model=SuggestionOut, status_code=201)
def suggest(payload: SuggestionInput, db: Db, user: CurrentUser):
    db.execute(select(User.id).where(User.id == user.id).with_for_update())
    require(
        not db.scalar(select(Skill.id).where(func.lower(Skill.name) == payload.name.lower())),
        "SKILL_EXISTS",
        "This skill already exists; select it from the catalog",
    )
    existing = db.scalar(
        select(SkillSuggestion).where(
            SkillSuggestion.user_id == user.id,
            SkillSuggestion.status == "PENDING",
            func.lower(SkillSuggestion.name) == payload.name.lower(),
        )
    )
    if existing:
        return existing
    item = SkillSuggestion(user_id=user.id, **payload.model_dump())
    db.add(item)
    db.commit()
    return item


def suggestion_page(db, statement, limit, offset):
    return Page(
        items=db.scalars(
            statement.order_by(SkillSuggestion.created_at.desc(), SkillSuggestion.id)
            .limit(limit)
            .offset(offset)
        ).all(),
        limit=limit,
        offset=offset,
    )


@router.get("/skill-suggestions", response_model=Page[SuggestionOut])
def mine(
    db: Db, user: CurrentUser, limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0)
):
    return suggestion_page(
        db, select(SkillSuggestion).where(SkillSuggestion.user_id == user.id), limit, offset
    )


@admin_router.get("/skill-suggestions", response_model=Page[SuggestionOut])
def all_suggestions(
    db: Db, admin: AdminUser, limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0)
):
    return suggestion_page(db, select(SkillSuggestion), limit, offset)


@admin_router.post("/skill-suggestions/{suggestion_id}/resolve", response_model=SuggestionOut)
def resolve(suggestion_id: str, payload: SuggestionDecision, db: Db, admin: AdminUser):
    # Catalog edits and suggestion resolutions share the hierarchy lock.
    db.execute(text("SELECT pg_advisory_xact_lock(715001)"))
    item = db.scalar(
        select(SkillSuggestion).where(SkillSuggestion.id == suggestion_id).with_for_update()
    )
    require(item is not None, "SUGGESTION_NOT_FOUND", "Suggestion is unavailable", 404)
    decision = payload.model_dump()
    if item.status != "PENDING":
        require(
            item.decision == decision, "ALREADY_RESOLVED", "Suggestion was resolved differently"
        )
        return item
    if payload.action == "APPROVE":
        if payload.skill_id:
            skill = db.get(Skill, payload.skill_id)
            require(skill is not None, "SKILL_NOT_FOUND", "Selected skill does not exist", 404)
        else:
            name = payload.name or item.name
            skill = db.scalar(select(Skill).where(func.lower(Skill.name) == name.lower()))
            if not skill:
                require(bool(payload.category), "CATEGORY_REQUIRED", "Choose a category", 422)
                validate_parent(db, payload.parent_id)
                skill = Skill(name=name, category=payload.category, parent_id=payload.parent_id)
                db.add(skill)
                db.flush()
        item.skill_id = skill.id
        item.status = "APPROVED"
    else:
        item.status = "REJECTED"
    item.resolution = payload.note
    item.decision = decision
    db.add(
        AuditRecord(
            admin_id=admin.id,
            action="RESOLVE_SKILL_SUGGESTION",
            resource_id=item.id,
            details=decision,
        )
    )
    db.add(
        Notification(
            user_id=item.user_id,
            resource_id=item.id,
            content=f"Your skill suggestion {item.name} was {item.status.lower()}: {payload.note}"[
                :500
            ],
        )
    )
    db.commit()
    return item


@admin_router.get("/users", response_model=Page[AdminMember])
def members(
    db: Db,
    admin: AdminUser,
    q: str = Query("", max_length=100),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    statement = select(User)
    if q:
        statement = statement.where(
            or_(User.name.icontains(q, autoescape=True), User.email.icontains(q, autoescape=True))
        )
    return Page(
        items=db.scalars(statement.order_by(User.name, User.id).limit(limit).offset(offset)).all(),
        limit=limit,
        offset=offset,
    )

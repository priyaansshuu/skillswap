from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select

from app.accounting import wallet
from app.config import get_settings
from app.errors import fail
from app.models import CreditEntry, User
from app.schemas import Me, ProfileUpdate, Register, Token
from app.security import CurrentUser, Db, dummy_hash, issue_token, password_hash, throttle

router = APIRouter(tags=["Accounts"])


def me_response(db, user):
    return Me(
        id=user.id,
        name=user.name,
        email=user.email,
        city=user.city,
        campus=user.campus,
        bio=user.bio,
        is_admin=user.is_admin,
        **wallet(db, user.id).model_dump(),
    )


@router.post("/auth/register", response_model=Me, status_code=201)
def register(payload: Register, request: Request, db: Db):
    email = str(payload.email).lower()
    throttle(db, request, email, "register")
    if db.scalar(select(User.id).where(User.email == email)):
        fail(409, "EMAIL_EXISTS", "This email is already registered")
    user = User(name=payload.name, email=email, password_hash=password_hash.hash(payload.password))
    db.add(user)
    db.flush()
    if get_settings().starter_minutes:
        db.add(
            CreditEntry(receiver_id=user.id, minutes=get_settings().starter_minutes, kind="GRANT")
        )
    db.commit()
    return me_response(db, user)


@router.post("/auth/token", response_model=Token)
def login(request: Request, db: Db, form: Annotated[OAuth2PasswordRequestForm, Depends()]):
    if len(form.username) > 254 or len(form.password) > 128:
        fail(401, "INVALID_CREDENTIALS", "Invalid email or password")
    email = form.username.strip().lower()
    throttle(db, request, email, "login")
    user = db.scalar(select(User).where(User.email == email))
    valid = password_hash.verify(form.password, user.password_hash if user else dummy_hash)
    if not valid or not user or not user.active:
        fail(401, "INVALID_CREDENTIALS", "Invalid email or password")
    return Token(access_token=issue_token(user.id))


@router.get("/me", response_model=Me)
def get_me(db: Db, user: CurrentUser):
    return me_response(db, user)


@router.patch("/me", response_model=Me)
def update_me(payload: ProfileUpdate, db: Db, user: CurrentUser):
    for field, value in payload.model_dump(exclude_unset=True).items():
        if field in {"name", "bio"} and value is None:
            fail(422, "INVALID_PROFILE", "Name and bio cannot be null")
        setattr(user, field, value)
    db.commit()
    return me_response(db, user)

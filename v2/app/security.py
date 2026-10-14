import hashlib
from datetime import timedelta
from typing import Annotated

import jwt
from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash
from sqlalchemy import delete
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.errors import fail
from app.models import AuthAttempt, User, new_id, now

password_hash = PasswordHash.recommended()
dummy_hash = password_hash.hash("Dummy-password-for-constant-login-verification")
oauth2 = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")
Db = Annotated[Session, Depends(get_db)]


def issue_token(user_id: str):
    issued = now()
    return jwt.encode(
        {
            "sub": user_id,
            "iat": issued,
            "exp": issued + timedelta(minutes=30),
            "iss": "skillswap",
            "aud": "skillswap-api",
            "jti": new_id(),
        },
        get_settings().jwt_secret.get_secret_value(),
        algorithm="HS256",
    )


def current_user(db: Db, token: Annotated[str, Depends(oauth2)]):
    try:
        claims = jwt.decode(
            token,
            get_settings().jwt_secret.get_secret_value(),
            algorithms=["HS256"],
            audience="skillswap-api",
            issuer="skillswap",
            options={"require": ["exp", "iat", "sub", "jti"]},
        )
    except jwt.InvalidTokenError:
        fail(401, "INVALID_TOKEN", "Please log in again")
    user = db.get(User, claims["sub"])
    if not user or not user.active:
        fail(401, "INACTIVE_ACCOUNT", "Account is unavailable")
    return user


CurrentUser = Annotated[User, Depends(current_user)]


def admin_user(user: CurrentUser):
    if not user.is_admin:
        fail(403, "ADMIN_REQUIRED", "Administrator access is required")
    return user


AdminUser = Annotated[User, Depends(admin_user)]


def throttle(db: Session, request: Request, identity: str, purpose: str):
    # Durable fixed-window limits. Ignore untrusted forwarded IP headers.
    ip = request.client.host if request.client else "local"
    bucket = int(now().timestamp()) // 900
    secret = get_settings().jwt_secret.get_secret_value()
    counts = []
    for raw, limit in [(f"{purpose}:ip:{ip}", 100), (f"{purpose}:identity:{ip}:{identity}", 20)]:
        key = hashlib.sha256((secret + raw).encode()).hexdigest()
        statement = insert(AuthAttempt).values(key=key, bucket=bucket, count=1)
        statement = statement.on_conflict_do_update(
            index_elements=[AuthAttempt.key, AuthAttempt.bucket],
            set_={"count": AuthAttempt.count + 1},
        ).returning(AuthAttempt.count)
        counts.append((db.scalar(statement), limit))
    db.execute(delete(AuthAttempt).where(AuthAttempt.bucket < bucket - 4))
    db.commit()  # Invalid credentials must also consume an attempt.
    if any(count > limit for count, limit in counts):
        fail(429, "AUTH_RATE_LIMIT", "Too many attempts; try again in 15 minutes")

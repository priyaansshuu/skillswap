"""Additional synthetic accounts, optionally starting with unfilled profiles."""

from datetime import timedelta
from uuid import NAMESPACE_URL, uuid5

from sqlalchemy import select

from app.config import get_settings
from app.models import Availability, CreditEntry, User, UserSkill
from app.security import password_hash

SKILLS = ["React", "JavaScript", "Python", "Mathematics", "English", "Guitar"]


def add_members(db, skills, start, password, count, *, blank=False):
    for index in range(count):
        prefix = "blank" if blank else "member"
        email = f"{prefix}{index + 1:02d}@example.com"
        expected_id = str(uuid5(NAMESPACE_URL, "skillswap-demo:user:" + email))
        user = db.scalar(select(User).where(User.email == email))
        if user and user.id != expected_id:
            raise ValueError(
                f"Reserved demo address already belongs to a non-demo account: {email}"
            )
        if not user:
            user = User(
                id=expected_id,
                name=f"Demo Account {index + 1:02d}" if blank else f"Demo Member {index + 1:02d}",
                email=email,
                password_hash=password_hash.hash(password),
                city=None if blank else ["Chennai", "Bengaluru", "Mumbai"][index % 3],
                campus=None if blank else "Demo College",
                bio=""
                if blank
                else "Synthetic demo member with both teaching offers and learning goals.",
            )
            db.add(user)
            db.flush()
            if get_settings().starter_minutes:
                db.add(
                    CreditEntry(
                        receiver_id=user.id, minutes=get_settings().starter_minutes, kind="GRANT"
                    )
                )
        if blank:
            # Existing users may have filled their profiles; never clear their choices.
            continue
        for kind, shift in [("OFFER", 0), ("WANT", 2)]:
            for offset in range(2):
                skill = skills[SKILLS[(index + shift + offset) % len(SKILLS)]]
                if not db.get(UserSkill, (user.id, skill.id, kind)):
                    db.add(
                        UserSkill(
                            user_id=user.id,
                            skill_id=skill.id,
                            kind=kind,
                            level=3 + index % 3 if kind == "OFFER" else 2 + index % 3,
                        )
                    )
        for mode in ["ONLINE", "IN_PERSON"]:
            if not db.scalar(
                select(Availability.id).where(
                    Availability.user_id == user.id,
                    Availability.mode == mode,
                    Availability.ends_at > start,
                )
            ):
                db.add(
                    Availability(
                        user_id=user.id,
                        starts_at=start,
                        ends_at=start + timedelta(hours=4),
                        mode=mode,
                    )
                )

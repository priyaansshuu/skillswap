import argparse
import getpass
import json
import os
from datetime import timedelta
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_engine
from app.models import (
    Availability,
    CreditEntry,
    ExchangeRequest,
    ExchangeSession,
    ReputationEvent,
    Review,
    Skill,
    User,
    UserSkill,
    now,
)
from app.schemas import Register
from app.security import password_hash


def demo_id(label):
    return str(uuid5(NAMESPACE_URL, "skillswap-demo:" + label))


def seed():
    password = os.environ.get("DEMO_PASSWORD") or getpass.getpass(
        "Choose a password for all synthetic demo accounts: "
    )
    Register(name="Demo", email="demo@example.com", password=password)
    with Session(get_engine()) as db:
        users = []
        for i in range(15):
            email = (
                ["admin@example.com", "learner@example.com", "teacher@example.com"][i]
                if i < 3
                else f"demo{i}@example.com"
            )
            user = db.scalar(select(User).where(User.email == email))
            if not user:
                user = User(
                    id=demo_id("user:" + email),
                    name=["Demo Admin", "Demo Learner", "Demo Teacher"][i]
                    if i < 3
                    else f"Demo Member {i}",
                    email=email,
                    password_hash=password_hash.hash(password),
                    city="Chennai",
                    campus="Demo College",
                    is_admin=i == 0,
                )
                db.add(user)
                db.flush()
                if get_settings().starter_minutes:
                    db.add(
                        CreditEntry(
                            receiver_id=user.id,
                            minutes=get_settings().starter_minutes,
                            kind="GRANT",
                        )
                    )
            users.append(user)
        db.flush()
        definitions = [
            ("Web Development", None),
            ("Frontend Development", "Web Development"),
            ("JavaScript", "Frontend Development"),
            ("React", "JavaScript"),
            ("Python", None),
            ("Pandas", "Python"),
            ("Machine Learning", "Python"),
            ("Mathematics", None),
            ("English", None),
            ("Guitar", None),
        ]
        skills = {}
        for name, parent in definitions:
            skill = db.scalar(select(Skill).where(Skill.name == name))
            if not skill:
                skill = Skill(
                    id=demo_id("skill:" + name),
                    name=name,
                    category="Technology"
                    if name not in {"English", "Guitar", "Mathematics"}
                    else "General",
                    parent_id=skills[parent].id if parent else None,
                )
                db.add(skill)
                db.flush()
            skills[name] = skill
        start = (now() + timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0)
        for i, user in enumerate(users[2:]):
            skill = skills[
                ["React", "JavaScript", "Python", "Mathematics", "English", "Guitar"][i % 6]
            ]
            if not db.get(UserSkill, (user.id, skill.id, "OFFER")):
                db.add(UserSkill(user_id=user.id, skill_id=skill.id, kind="OFFER", level=3 + i % 3))
            if not db.scalar(
                select(Availability.id).where(
                    Availability.user_id == user.id, Availability.ends_at > start
                )
            ):
                db.add(
                    Availability(
                        user_id=user.id,
                        starts_at=start,
                        ends_at=start + timedelta(hours=4),
                        mode="ONLINE",
                    )
                )
        if not db.get(UserSkill, (users[1].id, skills["React"].id, "WANT")):
            db.add(
                UserSkill(user_id=users[1].id, skill_id=skills["React"].id, kind="WANT", level=3)
            )
        for name in ["React", "Pandas"]:
            request_id = demo_id("open-request:" + name)
            request = db.get(ExchangeRequest, request_id)
            if not request:
                request = ExchangeRequest(
                    id=request_id,
                    learner_id=users[1].id,
                    skill_id=skills[name].id,
                    duration_minutes=60,
                    window_start=start,
                    window_end=start + timedelta(hours=3),
                    mode="ONLINE",
                )
                db.add(request)
            elif request.status == "OPEN" and request.window_start < now():
                request.window_start, request.window_end = start, start + timedelta(hours=3)
        # One explicitly synthetic completed exchange demonstrates joins, ledger and reputation.
        session_id = demo_id("historical-session")
        if not db.get(ExchangeSession, session_id) and get_settings().starter_minutes >= 60:
            historical_start = start - timedelta(days=3)
            request = ExchangeRequest(
                id=demo_id("historical-request"),
                learner_id=users[4].id,
                provider_id=users[2].id,
                skill_id=skills["React"].id,
                offered_skill_id=skills["React"].id,
                duration_minutes=60,
                window_start=historical_start,
                window_end=historical_start + timedelta(hours=1),
                selected_start=historical_start,
                mode="ONLINE",
                status="FULFILLED",
            )
            db.add(request)
            db.flush()
            session = ExchangeSession(
                id=session_id,
                request_id=request.id,
                learner_id=users[4].id,
                provider_id=users[2].id,
                skill_id=skills["React"].id,
                starts_at=historical_start,
                ends_at=historical_start + timedelta(hours=1),
                status="COMPLETED",
                actual_minutes=60,
                completed_at=historical_start + timedelta(hours=1),
            )
            db.add(session)
            db.flush()
            db.add(
                CreditEntry(
                    sender_id=users[4].id,
                    receiver_id=users[2].id,
                    session_id=session.id,
                    kind="TRANSFER",
                    minutes=60,
                )
            )
            review = Review(
                id=demo_id("historical-review"),
                session_id=session.id,
                reviewer_id=users[4].id,
                reviewee_id=users[2].id,
                stars=5,
                comment="Synthetic demo feedback",
                created_at=session.completed_at,
            )
            db.add(review)
            db.add_all(
                [
                    ReputationEvent(
                        user_id=users[2].id,
                        skill_id=session.skill_id,
                        session_id=session.id,
                        source_key="completion:" + session.id,
                        kind="COMPLETION",
                        delta=2,
                        created_at=session.completed_at,
                    ),
                    ReputationEvent(
                        user_id=users[2].id,
                        skill_id=session.skill_id,
                        session_id=session.id,
                        source_key="review:" + review.id,
                        kind="REVIEW",
                        delta=10,
                        created_at=session.completed_at + timedelta(seconds=1),
                    ),
                ]
            )
        db.commit()
        print("Seed complete: 15 synthetic accounts, 10 skills, exact and fallback requests.")
        print(
            "Accounts: admin@example.com, learner@example.com, teacher@example.com (password you supplied)."
        )
        print(
            "Existing accounts and passwords were preserved. Re-running seed does not duplicate credits."
        )


def create_admin():
    account = Register(
        name=input("Admin name: "),
        email=input("Admin email: "),
        password=getpass.getpass("Admin password: "),
    )
    with Session(get_engine()) as db:
        if db.scalar(select(User.id).where(User.email == str(account.email).lower())):
            raise ValueError(
                "Email already exists; this command does not silently promote existing users"
            )
        user = User(
            name=account.name,
            email=str(account.email).lower(),
            password_hash=password_hash.hash(account.password),
            is_admin=True,
        )
        db.add(user)
        db.flush()
        if get_settings().starter_minutes:
            db.add(
                CreditEntry(
                    receiver_id=user.id, minutes=get_settings().starter_minutes, kind="GRANT"
                )
            )
        db.commit()
    print("Administrator created.")


def export_openapi(path):
    from app.main import app

    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(app.openapi(), indent=2), encoding="utf-8")
    print("OpenAPI exported.")


def evaluate(request_id, labels_path, output_path):
    from app.evaluation import compare_models

    with Session(get_engine()) as db:
        request = db.get(ExchangeRequest, request_id)
        if not request:
            raise ValueError("Request does not exist")
        report = compare_models(db, request).model_dump(mode="json")
    if labels_path:
        labels = json.loads(Path(labels_path).read_text(encoding="utf-8"))
        if not isinstance(labels, dict) or any(type(v) is not bool for v in labels.values()):
            raise ValueError("Labels must map provider IDs to explicit true/false relevance")
        for model in report["models"]:
            ranked = model["candidates"]
            if any(c["provider_id"] not in labels for c in ranked):
                raise ValueError("Every retrieved provider needs an explicit relevance label")
            model["precision_at_5"] = sum(labels[c["provider_id"]] for c in ranked[:5]) / 5
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("Evaluation exported; synthetic rankings are not experimental findings.")


def main():
    from dotenv import load_dotenv

    load_dotenv()
    parser = argparse.ArgumentParser(
        description="SkillSwap local administration and demo utilities"
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("seed")
    sub.add_parser("create-admin")
    export = sub.add_parser("export-openapi")
    export.add_argument("--output", default="docs/openapi.json")
    evaluation = sub.add_parser("evaluate")
    evaluation.add_argument("request_id")
    evaluation.add_argument("--labels")
    evaluation.add_argument("--output", default="docs/evaluation.json")
    args = parser.parse_args()
    if args.command == "seed":
        seed()
    elif args.command == "create-admin":
        create_admin()
    elif args.command == "export-openapi":
        export_openapi(args.output)
    else:
        evaluate(args.request_id, args.labels, args.output)


if __name__ == "__main__":
    main()

from datetime import datetime
from typing import Annotated, Generic, Literal, TypeVar

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    StringConstraints,
    model_validator,
)


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Output(BaseModel):
    model_config = ConfigDict(from_attributes=True)


T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: list[T]
    limit: int
    offset: int


class Register(Input):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: Annotated[
        str, StringConstraints(strip_whitespace=False, min_length=12, max_length=128)
    ]


class ProfileUpdate(Input):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    city: str | None = Field(default=None, max_length=100)
    campus: str | None = Field(default=None, max_length=100)
    bio: str | None = Field(default=None, max_length=1000)


class PublicProfile(Output):
    id: str
    name: str
    city: str | None
    campus: str | None
    bio: str


class Me(PublicProfile):
    email: str
    is_admin: bool
    balance_minutes: int
    reserved_minutes: int
    available_minutes: int
    taught_minutes: int


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 1800


class SkillInput(Input):
    name: str = Field(min_length=1, max_length=100)
    category: str = Field(min_length=1, max_length=100)
    parent_id: str | None = None


class SkillOut(Output):
    id: str
    name: str
    category: str
    parent_id: str | None


class UserSkillInput(Input):
    skill_id: str
    kind: Literal["OFFER", "WANT"]
    level: int = Field(ge=1, le=5)


class UserSkillOut(Output):
    user_id: str
    skill_id: str
    kind: str
    level: int


class AvailabilityInput(Input):
    starts_at: AwareDatetime
    ends_at: AwareDatetime
    mode: Literal["ONLINE", "IN_PERSON"] = "ONLINE"

    @model_validator(mode="after")
    def valid_interval(self):
        if self.ends_at <= self.starts_at or (self.ends_at - self.starts_at).days > 30:
            raise ValueError("Availability must be positive and no longer than 30 days")
        return self


class AvailabilityOut(Output):
    id: str
    starts_at: datetime
    ends_at: datetime
    mode: str


class RequestInput(Input):
    skill_id: str
    provider_id: str | None = None
    duration_minutes: int = Field(ge=1, le=480)
    window_start: AwareDatetime
    window_end: AwareDatetime
    mode: Literal["ONLINE", "IN_PERSON"] = "ONLINE"

    @model_validator(mode="after")
    def valid_window(self):
        seconds = (self.window_end - self.window_start).total_seconds()
        if seconds < self.duration_minutes * 60 or seconds > 30 * 86400:
            raise ValueError("Window must fit the duration and be no longer than 30 days")
        return self


class RequestOut(Output):
    id: str
    learner_id: str
    provider_id: str | None
    skill_id: str
    offered_skill_id: str | None
    duration_minutes: int
    window_start: datetime
    window_end: datetime
    selected_start: datetime | None
    mode: str
    status: str
    created_at: datetime


class Selection(Input):
    candidate_id: str


class MatchOut(Output):
    id: str
    provider_id: str
    offered_skill_id: str
    score: float
    factors: dict[str, float]
    suggested_start: datetime
    hierarchy_distance: int


class MatchResults(BaseModel):
    run_id: str
    algorithm: str
    weights: dict[str, float]
    candidates: list[MatchOut]


class SessionOut(Output):
    id: str
    request_id: str
    learner_id: str
    provider_id: str
    skill_id: str
    starts_at: datetime
    ends_at: datetime
    status: str
    actual_minutes: int | None
    completed_at: datetime | None


class ConfirmInput(Input):
    minutes: int = Field(ge=1, le=480)


class ConfirmationOut(Output):
    user_id: str
    minutes: int


class ReviewInput(Input):
    stars: int = Field(ge=1, le=5)
    comment: str = Field(default="", max_length=2000)


class ReviewOut(Output):
    id: str
    session_id: str
    reviewer_id: str
    reviewee_id: str
    stars: int
    comment: str
    created_at: datetime


class Wallet(BaseModel):
    balance_minutes: int
    reserved_minutes: int
    available_minutes: int
    taught_minutes: int


class CreditOut(Output):
    id: str
    sender_id: str | None
    receiver_id: str
    session_id: str | None
    reversal_of: str | None
    kind: str
    minutes: int
    created_at: datetime


class ReputationOut(BaseModel):
    user_id: str
    skill_id: str | None
    score: float
    event_count: int
    half_life_days: float
    as_of: datetime


class NotificationOut(Output):
    id: str
    content: str
    resource_id: str | None
    is_read: bool
    created_at: datetime


class DisputeInput(Input):
    reason: str = Field(min_length=10, max_length=2000)


class DisputeOut(Output):
    id: str
    session_id: str
    reporter_id: str
    reason: str
    previous_status: str
    status: str
    resolution: str | None
    created_at: datetime


class ResolveInput(Input):
    action: Literal["DISMISS", "CANCEL", "REVERSE"]
    note: str = Field(min_length=10, max_length=2000)
    penalty: Literal["NONE", "NO_SHOW", "UNJUSTIFIED_CANCELLATION"] = "NONE"
    responsible_user_id: str | None = None

    @model_validator(mode="after")
    def penalty_target(self):
        if (self.penalty == "NONE") != (self.responsible_user_id is None):
            raise ValueError("A verified penalty requires the responsible participant")
        return self


class ModerateInput(Input):
    active: bool
    reason: str = Field(min_length=10, max_length=1000)


class AuditOut(Output):
    id: str
    admin_id: str
    action: str
    resource_id: str
    details: dict
    created_at: datetime


class ProviderOffer(Output):
    skill_id: str
    name: str
    category: str
    level: int


class ProviderProfile(PublicProfile):
    offers: list[ProviderOffer]
    modes: list[str]
    rating_average: float | None
    rating_count: int
    reputation_score: float


class PreviewCandidate(BaseModel):
    provider: ProviderProfile
    offered_skill_id: str
    suggested_start: datetime
    score: float
    hierarchy_distance: int


class RequestPreview(BaseModel):
    eligible: bool
    reason: str | None
    available_minutes: int
    candidates: list[PreviewCandidate]


class SuggestionInput(Input):
    name: str = Field(min_length=1, max_length=100)
    explanation: str = Field(default="", max_length=1000)


class SuggestionOut(Output):
    id: str
    user_id: str
    name: str
    explanation: str
    status: str
    skill_id: str | None
    resolution: str | None
    created_at: datetime


class SuggestionDecision(Input):
    action: Literal["APPROVE", "REJECT"]
    name: str | None = Field(default=None, min_length=1, max_length=100)
    category: str | None = Field(default=None, min_length=1, max_length=100)
    parent_id: str | None = None
    skill_id: str | None = None
    note: str = Field(min_length=5, max_length=1000)


class AdminMember(PublicProfile):
    email: str
    active: bool
    is_admin: bool

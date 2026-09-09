import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    display_name: str = Field(min_length=1, max_length=80)

    @field_validator("password")
    @classmethod
    def _password_strength(cls, v: str) -> str:
        if v.isdigit() or v.isalpha():
            raise ValueError("Password must include a mix of letters and numbers")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    is_verified: bool


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
    user: UserOut


class LearnerProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    display_name: str
    current_level: str
    learning_goal: str | None
    daily_goal_minutes: int
    onboarding_completed: bool
    current_streak: int
    longest_streak: int
    total_xp: int


class LearnerProfileUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=80)
    learning_goal: str | None = None
    daily_goal_minutes: int | None = Field(default=None, ge=1, le=240)
    onboarding_completed: bool | None = None

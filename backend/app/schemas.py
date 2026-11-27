from typing import Literal
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
    field_validator
)
from app.utils.validators import (
    validate_email,
    PROGRAMS
)
from datetime import date
from app.config import CLEARANCE_WORKING_DAYS

Office = Literal[
    "REGISTRAR",
    "LIBRARY",
    "ACCOUNTING",
    "STUDENT_AFFAIRS"
]

ClearanceStatus = Literal[
    "CLEARED",
    "HOLD"
]

class StrictSchema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        strict=True
    )



class LoginRequest(StrictSchema):
    username: str = Field(
        min_length=3,
        max_length=80,
        pattern=r"^[A-Za-z0-9_.@-]+$"
    )

    password: str = Field(
        min_length=1,
        max_length=128,
        repr=False
    )


class ClearanceUpdate(StrictSchema):
    status: Literal["CLEARED", "HOLD"]

    reason: str | None = Field(
        default=None,
        max_length=500
    )

    @model_validator(mode="after")
    def validate_reason(self):
        if self.status == "HOLD":
            if not self.reason or not self.reason.strip():
                raise ValueError(
                    "A HOLD must have a reason."
                )

            self.reason = self.reason.strip()

        elif self.reason is not None:
            raise ValueError(
                "CLEARED records must not have a hold reason."
            )

        return self
#extended schema so that the validation requiring reason still hold    
class ClearanceRecordInput(ClearanceUpdate):
    student_id: str = Field(
        pattern=r"^[0-9]{4}-[0-9]{4}$"
    )

    period_id: int = Field(gt=0)

    office: Office

class StudentRecord(StrictSchema):
    student_id: str = Field(
        pattern=r"^[0-9]{4}-[0-9]{4}$"
    )

    full_name: str = Field(
        min_length=1,
        max_length=150
    )

    program: str = Field(
        min_length=1,
        max_length=20
    )

    year_level: int = Field(
        ge=1,
        le=4
    )

    email: str = Field(
        min_length=3,
        max_length=255
    )

    @field_validator("email")
    @classmethod
    def check_email(cls, value):
        if not validate_email(value):
            raise ValueError("Invalid email address.")

        return value.strip()

    @field_validator("program")
    @classmethod
    def check_program(cls, value):
        if value not in PROGRAMS:
            raise ValueError("Unknown program code.")

        return value

    @field_validator("full_name")
    @classmethod
    def check_name(cls, value):
        value = value.strip()

        if not value:
            raise ValueError("Name cannot be empty.")

        return value


#TOKEN AUTHENTICATION

class TokenResponse(StrictSchema):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int


class UserResponse(StrictSchema):
    user_id: int
    username: str

    role: Literal[
        "STUDENT",
        "STAFF",
        "ADMIN"
    ]

    student_id: str | None = None
    office: Office | None = None


class MessageResponse(StrictSchema):
    message: str


#CLEARANCE PERIOD
class ClearancePeriodCreate(StrictSchema):
    name: str = Field(
        min_length=1,
        max_length=100
    )

    start_date: str = Field(
        pattern=r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    )

    working_days: int = Field(
        default=CLEARANCE_WORKING_DAYS,
        ge=1,
        le=365
    )

    @field_validator("name")
    @classmethod
    def validate_period_name(cls, value):
        value = value.strip()

        if not value or not value.isprintable():
            raise ValueError("Invalid period name.")

        return value

    @field_validator("start_date")
    @classmethod
    def validate_start_date(cls, value):
        try:
            parsed = date.fromisoformat(value)

        except ValueError:
            raise ValueError(
                "Invalid calendar date."
            ) from None

        if not 2000 <= parsed.year <= 2098:
            raise ValueError(
                "Unsupported starting year."
            )

        return parsed.isoformat()

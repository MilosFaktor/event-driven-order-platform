from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, RootModel, field_validator


class Notification(BaseModel):
    model_config = ConfigDict(
        extra="forbid", validate_assignment=True, str_strip_whitespace=True
    )

    notification_id: str
    order_id: str
    customer_id: str
    channel: Literal["email"] = "email"
    type: str
    status: Literal["PENDING", "SENT", "FAILED"] = "PENDING"
    message: str = Field(default="", max_length=1000)

    @field_validator("notification_id")
    @classmethod
    def ensure_notification_id_starts_with_ntf(cls, v: str) -> str:
        if not v.startswith("ntf_"):
            raise ValueError("Notification ID must start with 'ntf_'")
        return v


class Notifications(RootModel[dict[str, Notification]]):
    pass

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, RootModel


class Notification(BaseModel):
    model_config = ConfigDict(
        extra="forbid", validate_assignment=True, str_strip_whitespace=True
    )

    notification_id: str
    order_id: str
    customer_id: str
    channel: str
    type: str
    status: Literal["PENDING", "SENT", "FAILED"] = "PENDING"
    message: str = Field(default="", max_length=1000)


class Notifications(RootModel[dict[str, Notification]]):
    pass

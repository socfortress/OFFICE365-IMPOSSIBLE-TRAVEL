from typing import Optional

from pydantic import BaseModel
from pydantic import Extra
from pydantic import Field


class EventShipperPayload(BaseModel):
    host: str = Field(
        ...,
        description="The host name of Graylog.",
        examples="127.0.0.1",
    )
    port: str = Field(
        ...,
        description="The port number of Graylog GELF Input.",
        examples="12201",
    )
    integration: str = Field(
        ...,
        description="The integration name.",
        examples="mimecast",
    )
    customer_code: str = Field(
        ...,
        description="The customer code.",
        examples="socfortress",
    )

    class Config:
        extra = Extra.allow

    def to_dict(self):
        return self.dict(exclude_none=True)


class EventShipperPayloadResponse(BaseModel):
    message: str
    success: bool
    data: Optional[dict] = Field(
        None,
        description="The Event Shipper response data.",
    )

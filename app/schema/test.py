from fastapi import HTTPException
from pydantic import BaseModel
from pydantic import Field
from pydantic import validator


class TestRequest(BaseModel):
    integration: str = Field(..., example="mimecast")
    customer_code: str = Field(..., example="socfortress")
    api_cred: str = Field(..., example="1234567890")
    graylog_host: str = Field(..., example="127.0.0.1")
    graylog_port: str = Field(..., example=12201)

    @validator("integration")
    def check_integration(cls, v):
        if v != "mimecast":
            raise HTTPException(
                status_code=400,
                detail="Invalid integration. Only 'mimecast' is supported.",
            )
        return v


class TestResponse(BaseModel):
    message: str
    success: bool

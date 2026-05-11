from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    detail: str = Field(description="Human readable error description")
    error_code: str = Field(description="Domain error class name")

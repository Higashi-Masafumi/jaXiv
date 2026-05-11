from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """FastAPI standard error envelope returned for translation failures."""

    detail: str = Field(description="Human readable error description")

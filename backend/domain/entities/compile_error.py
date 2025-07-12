from pydantic import BaseModel, Field, StrictStr
from enum import Enum


class CompileErrorType(Enum):
    """
    The type of compile error.
    """

    COMPILE_ERROR = "compile_error"
    COMPILE_TIMEOUT = "compile_timeout"


class CompileError(BaseModel):
    """
    The error of compile.
    """

    error_type: CompileErrorType = Field(description="The type of compile error.")
    error_message: StrictStr = Field(description="The message of compile error.")

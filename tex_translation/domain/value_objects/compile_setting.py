from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, StrictStr


class CompileSetting(BaseModel):
    """LaTeX compile settings."""

    model_config = ConfigDict(frozen=True)

    engine: Literal["pdflatex", "xelatex", "lualatex"] = Field(default="pdflatex")
    use_bibtex: bool = Field(default=True)
    target_file_name: StrictStr = Field(...)
    source_directory: StrictStr = Field(...)

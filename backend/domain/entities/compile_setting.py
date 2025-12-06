from typing import Literal

from pydantic import BaseModel, Field, StrictStr


class CompileSetting(BaseModel):
    """
    A compile setting.
    """

    engine: Literal["pdflatex", "xelatex", "lualatex"] = Field(
        default="pdflatex",
        description="The engine to use for compiling the latex file.",
    )

    use_bibtex: bool = Field(
        default=True,
        description="Whether to use bibtex for compiling the latex file.",
    )

    target_file_name: StrictStr = Field(
        ...,
        description="The name of the target file.",
    )

    source_directory: StrictStr = Field(
        ...,
        description="The directory of the source file.",
    )

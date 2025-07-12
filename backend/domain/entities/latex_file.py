from pydantic import BaseModel, StrictStr, Field


class LatexFile(BaseModel):
    """
    A latex file.
    """

    path: StrictStr = Field(description="The path of the latex file")
    content: StrictStr = Field(description="The content of the latex file")


class TranslatedPdfFile(BaseModel):
    """
    A translated pdf file.
    """

    path: StrictStr = Field(description="The path of the translated pdf file")
    storage_path: StrictStr = Field(
        description="The path of the translated pdf file in the storage"
    )

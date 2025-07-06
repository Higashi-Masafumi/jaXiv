from pydantic import BaseModel, StrictStr


class LatexFile(BaseModel):
    """
    A latex file.
    """

    path: StrictStr
    content: StrictStr
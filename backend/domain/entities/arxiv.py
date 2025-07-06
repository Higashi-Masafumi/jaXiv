from pydantic import RootModel


class ArxivPaperId(RootModel[str]):
    root: str

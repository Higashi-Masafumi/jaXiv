from pydantic import RootModel, ConfigDict, field_validator


class Embedding(RootModel[list[float]]):
    """An embedding is a list of floats."""

    model_config = ConfigDict(frozen=True)

    @field_validator("root")
    @classmethod
    def validate_embedding(cls, v: list[float]) -> list[float]:
        if len(v) != 384:
            raise ValueError("Embedding must be a list of 384 floats.")
        return v

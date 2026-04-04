from pydantic import RootModel, ConfigDict


class Embedding(RootModel[list[float]]):
	"""An embedding is a list of floats."""

	model_config = ConfigDict(frozen=True)

	def __init__(self, embedding: list[float]):
		super().__init__(root=embedding)

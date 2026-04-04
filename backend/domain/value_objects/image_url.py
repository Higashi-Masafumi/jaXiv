from pydantic import ConfigDict, HttpUrl, RootModel


class ImageUrl(RootModel[HttpUrl]):
	"""Value Object representing an image URL."""

	model_config = ConfigDict(frozen=True)

	def __init__(self, url: str | HttpUrl) -> None:
		super().__init__(root=HttpUrl(url))

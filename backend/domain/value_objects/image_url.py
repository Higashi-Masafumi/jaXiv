from pydantic import ConfigDict, HttpUrl, RootModel


class ImageUrl(RootModel[HttpUrl]):
	"""Value Object representing an image URL."""

	model_config = ConfigDict(frozen=True)

	def __init__(self, url: HttpUrl):
		super().__init__(root=url)

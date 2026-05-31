from abc import ABC, abstractmethod


class IFigureQueryGenerator(ABC):
	"""Gateway that expands a free-form user description into image search queries.

	Used by the figure-suggestion feature: given a description of the research
	content or the figure the user wants to create, it produces several diverse
	search queries optimized for caption-based vector search over the figure
	collection.
	"""

	@abstractmethod
	async def generate_queries(self, user_input: str, n: int = 4) -> list[str]:
		"""Generate up to ``n`` diverse search queries from the user's input."""
		...

from logging import getLogger
from typing import ClassVar

from pydantic import BaseModel, ConfigDict

from application.unit_of_works import DigestUnitOfWork
from domain.gateways import DigestItem, IEmailGateway


class DigestRunResult(BaseModel):
	model_config = ConfigDict(frozen=True)

	sent: int
	skipped: int
	failed: int


class SendWeeklyDigestsUseCase:
	"""Emails each active subscriber the new arXiv posts matching their keywords.

	Each subscriber is processed in its own UoW block so a failure mid-run does not
	roll back deliveries already committed for earlier subscribers. Emails are sent
	before deliveries are recorded, so a crash between the two only risks a duplicate
	next run (never a silently skipped paper).
	"""

	MAX_ITEMS_PER_DIGEST: ClassVar[int] = 5

	def __init__(self, uow: DigestUnitOfWork, email_gateway: IEmailGateway) -> None:
		self._uow = uow
		self._email = email_gateway
		self._logger = getLogger(__name__)

	async def execute(self) -> DigestRunResult:
		async with self._uow as uow:
			subscriptions = await uow.topic_subscriptions.list_active()

		sent = 0
		skipped = 0
		failed = 0
		for subscription in subscriptions:
			if not subscription.keywords:
				skipped += 1
				continue
			try:
				async with self._uow as uow:
					email = await uow.auth_users.find_email(subscription.user_id)
					if not email:
						skipped += 1
						continue
					delivered_ids = await uow.digest_deliveries.find_delivered_blog_ids(
						subscription.user_id
					)
					matches = await uow.blog_posts.find_matching_arxiv(
						keywords=subscription.keywords,
						exclude_ids=delivered_ids,
						limit=self.MAX_ITEMS_PER_DIGEST,
					)
					if not matches:
						skipped += 1
						continue
					items = [
						DigestItem(paper_id=m.paper_id, title=m.title, summary=m.summary)
						for m in matches
					]
					await self._email.send_weekly_digest(to=email, items=items)
					await uow.digest_deliveries.record_deliveries(
						subscription.user_id, [m.id for m in matches]
					)
					sent += 1
			except Exception:
				self._logger.exception('Failed to deliver digest to %s', subscription.user_id)
				failed += 1
		return DigestRunResult(sent=sent, skipped=skipped, failed=failed)

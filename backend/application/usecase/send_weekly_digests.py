from logging import getLogger
from typing import ClassVar

from pydantic import BaseModel, ConfigDict

from application.unit_of_works import DigestUnitOfWork
from domain.gateways import DigestItem, IEmailGateway
from domain.repositories import ITopicSubscriptionRepository


class DigestRunResult(BaseModel):
	model_config = ConfigDict(frozen=True)

	sent: int
	skipped: int
	failed: int


class SendWeeklyDigestsUseCase:
	"""Emails each active subscriber the new arXiv posts matching their keywords.

	The active subscriptions are read up front (plain read, no transaction). Each
	subscriber's delivery — read matches, send, record — runs in its own UoW block
	so it commits atomically and one failure does not roll back earlier subscribers.
	The email is sent before the delivery is recorded, so a crash between the two
	only risks a duplicate next run (never a silently skipped paper).
	"""

	MAX_ITEMS_PER_DIGEST: ClassVar[int] = 5

	def __init__(
		self,
		topic_subscription_repository: ITopicSubscriptionRepository,
		digest_unit_of_work: DigestUnitOfWork,
		email_gateway: IEmailGateway,
	) -> None:
		self._subscriptions = topic_subscription_repository
		self._uow = digest_unit_of_work
		self._email = email_gateway
		self._logger = getLogger(__name__)

	async def execute(self) -> DigestRunResult:
		subscriptions = await self._subscriptions.list_active()
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

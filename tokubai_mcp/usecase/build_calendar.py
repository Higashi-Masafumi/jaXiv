from __future__ import annotations

from collections import defaultdict
from datetime import date

from domain.entities.calendar import CalendarDay, DealCalendar
from domain.entities.deal import Deal
from domain.errors.errors import StoreNotFoundError
from domain.gateways.deal_provider import DealProvider
from domain.gateways.store_repository import StoreRepository


class BuildCalendarUseCase:
    """登録店舗 (または指定店舗) の特売カレンダーを期間で組み立てる。"""

    def __init__(self, repository: StoreRepository, provider: DealProvider) -> None:
        self._repository = repository
        self._provider = provider

    def execute(
        self,
        start: date,
        end: date,
        store_ids: list[str] | None = None,
    ) -> DealCalendar:
        if start > end:
            start, end = end, start

        if store_ids is None:
            stores = self._repository.list_all()
        else:
            stores = []
            for sid in store_ids:
                store = self._repository.get(sid)
                if store is None:
                    raise StoreNotFoundError(sid)
                stores.append(store)

        by_date: dict[date, list[Deal]] = defaultdict(list)
        for store in stores:
            for deal in self._provider.deals_for(store, start, end):
                by_date[deal.on].append(deal)

        days = [
            CalendarDay(on=d, deals=sorted(by_date[d], key=lambda x: x.store_id))
            for d in sorted(by_date)
        ]
        return DealCalendar(start=start, end=end, days=days)

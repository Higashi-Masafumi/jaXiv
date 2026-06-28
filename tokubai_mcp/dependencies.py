from __future__ import annotations

from functools import lru_cache

from domain.gateways.deal_provider import DealProvider
from domain.gateways.store_repository import StoreRepository
from infrastructure.memory.store_repository import InMemoryStoreRepository
from infrastructure.sample.deal_provider import RuleBasedDealProvider
from infrastructure.sample.store_catalog import SAMPLE_STORE_CATALOG
from usecase.build_calendar import BuildCalendarUseCase
from usecase.find_best_day import FindBestDayUseCase
from usecase.register_store import RegisterStoreUseCase
from usecase.search_stores import SearchStoresUseCase


@lru_cache
def get_store_repository() -> StoreRepository:
    return InMemoryStoreRepository(catalog=SAMPLE_STORE_CATALOG)


@lru_cache
def get_deal_provider() -> DealProvider:
    return RuleBasedDealProvider()


def get_register_store_use_case() -> RegisterStoreUseCase:
    return RegisterStoreUseCase(repository=get_store_repository())


def get_search_stores_use_case() -> SearchStoresUseCase:
    return SearchStoresUseCase(repository=get_store_repository())


def get_build_calendar_use_case() -> BuildCalendarUseCase:
    return BuildCalendarUseCase(
        repository=get_store_repository(), provider=get_deal_provider()
    )


def get_find_best_day_use_case() -> FindBestDayUseCase:
    return FindBestDayUseCase(
        repository=get_store_repository(), provider=get_deal_provider()
    )

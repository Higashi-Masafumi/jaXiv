from __future__ import annotations

from datetime import date

import pytest

from domain.entities.deal import DealKind
from domain.errors.errors import StoreNotFoundError, UnknownChainError
from infrastructure.memory.store_repository import InMemoryStoreRepository
from infrastructure.sample.deal_provider import RuleBasedDealProvider
from infrastructure.sample.store_catalog import SAMPLE_STORE_CATALOG
from usecase.build_calendar import BuildCalendarUseCase
from usecase.find_best_day import FindBestDayUseCase
from usecase.register_store import RegisterStoreIn, RegisterStoreUseCase
from usecase.search_stores import SearchStoresUseCase


@pytest.fixture
def repo() -> InMemoryStoreRepository:
    return InMemoryStoreRepository(catalog=SAMPLE_STORE_CATALOG)


@pytest.fixture
def provider() -> RuleBasedDealProvider:
    return RuleBasedDealProvider()


def _register_aeon(repo: InMemoryStoreRepository) -> None:
    RegisterStoreUseCase(repo).execute(
        RegisterStoreIn(
            id="my-aeon",
            name="近所のイオン",
            chain_id="aeon",
            latitude=35.61,
            longitude=139.75,
        )
    )


def test_register_unknown_chain_raises(repo: InMemoryStoreRepository) -> None:
    with pytest.raises(UnknownChainError):
        RegisterStoreUseCase(repo).execute(
            RegisterStoreIn(
                id="x",
                name="謎スーパー",
                chain_id="not-a-chain",
                latitude=35.0,
                longitude=139.0,
            )
        )


def test_search_nearby_sorted_by_distance(repo: InMemoryStoreRepository) -> None:
    # 五反田駅付近を基準に半径 5km
    results = SearchStoresUseCase(repo).execute(
        latitude=35.6258, longitude=139.7237, radius_km=5.0, limit=10
    )
    assert results, "近隣店舗が見つかるはず"
    distances = [r.distance_km for r in results]
    assert distances == sorted(distances)


def test_aeon_kansha_day_is_5_percent_off(
    repo: InMemoryStoreRepository, provider: RuleBasedDealProvider
) -> None:
    _register_aeon(repo)
    calendar = BuildCalendarUseCase(repo, provider).execute(
        start=date(2026, 6, 1), end=date(2026, 6, 30)
    )
    by_date = {day.on: day for day in calendar.days}

    # 6/20 はお客様感謝デー 5% OFF
    assert date(2026, 6, 20) in by_date
    day20 = by_date[date(2026, 6, 20)]
    assert any(
        d.kind is DealKind.DISCOUNT_DAY and d.discount_percent == 5.0
        for d in day20.deals
    )
    assert day20.max_discount_percent == 5.0

    # 6/10 はありが10デー (ポイント 5 倍)
    day10 = by_date[date(2026, 6, 10)]
    assert any(
        d.kind is DealKind.POINT_DAY and d.point_multiplier == 5.0 for d in day10.deals
    )


def test_calendar_only_includes_days_with_deals(
    repo: InMemoryStoreRepository, provider: RuleBasedDealProvider
) -> None:
    _register_aeon(repo)
    calendar = BuildCalendarUseCase(repo, provider).execute(
        start=date(2026, 6, 1), end=date(2026, 6, 30)
    )
    # 全ての日に必ず deal があり、空の日は含まれない
    assert all(day.has_deals for day in calendar.days)


def test_build_calendar_unknown_store_raises(
    repo: InMemoryStoreRepository, provider: RuleBasedDealProvider
) -> None:
    with pytest.raises(StoreNotFoundError):
        BuildCalendarUseCase(repo, provider).execute(
            start=date(2026, 6, 1),
            end=date(2026, 6, 30),
            store_ids=["does-not-exist"],
        )


def test_find_best_day_ranks_kansha_day_highest(
    repo: InMemoryStoreRepository, provider: RuleBasedDealProvider
) -> None:
    _register_aeon(repo)
    scores = FindBestDayUseCase(repo, provider).execute(
        start=date(2026, 6, 1), end=date(2026, 6, 30), limit=3
    )
    assert scores
    # 5% OFF の感謝デー(20/30 日)が、ポイント5倍(=実効4%)より上位に来る
    top = scores[0]
    assert top.best_discount_percent == 5.0
    assert top.effective_discount_percent >= scores[-1].effective_discount_percent

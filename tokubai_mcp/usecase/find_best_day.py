from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from domain.entities.deal import Deal
from domain.gateways.deal_provider import DealProvider
from domain.gateways.store_repository import StoreRepository
from usecase.build_calendar import BuildCalendarUseCase


class DayScore(BaseModel):
    """ある日付の「お得さ」スコア。"""

    model_config = ConfigDict(frozen=True)

    on: date
    effective_discount_percent: float = Field(
        description="割引率 + ポイント還元を割引換算した合算値 (%)"
    )
    best_discount_percent: float
    best_point_multiplier: float
    deals: list[Deal]


class FindBestDayUseCase:
    """期間内で最もお得な買い物日をランキングする。

    実効割引率 = 最大割引率(%) + (最大ポイント倍率 - 1) × 基本ポイント率(%)
    として概算する。基本ポイント率の既定は 1.0%。
    """

    def __init__(
        self,
        repository: StoreRepository,
        provider: DealProvider,
        base_point_rate_percent: float = 1.0,
    ) -> None:
        self._calendar = BuildCalendarUseCase(repository, provider)
        self._base_point_rate = base_point_rate_percent

    def execute(
        self,
        start: date,
        end: date,
        store_ids: list[str] | None = None,
        limit: int = 5,
    ) -> list[DayScore]:
        calendar = self._calendar.execute(start, end, store_ids)

        scores = [
            DayScore(
                on=day.on,
                effective_discount_percent=round(
                    day.max_discount_percent
                    + (day.max_point_multiplier - 1.0) * self._base_point_rate,
                    2,
                ),
                best_discount_percent=day.max_discount_percent,
                best_point_multiplier=day.max_point_multiplier,
                deals=day.deals,
            )
            for day in calendar.days
        ]
        scores.sort(key=lambda s: (-s.effective_discount_percent, s.on))
        return scores[:limit]

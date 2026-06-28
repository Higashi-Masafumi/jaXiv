from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from domain.entities.deal import Deal


class CalendarDay(BaseModel):
    """カレンダー 1 日分。その日に有効な特売・ポイント施策を束ねる。"""

    model_config = ConfigDict(frozen=True)

    on: date
    deals: list[Deal] = Field(default_factory=list)

    @property
    def has_deals(self) -> bool:
        return len(self.deals) > 0

    @property
    def max_discount_percent(self) -> float:
        return max(
            (d.discount_percent or 0.0 for d in self.deals),
            default=0.0,
        )

    @property
    def max_point_multiplier(self) -> float:
        return max(
            (d.point_multiplier or 1.0 for d in self.deals),
            default=1.0,
        )


class DealCalendar(BaseModel):
    """期間内の日次カレンダー。特売がある日のみを保持する。"""

    model_config = ConfigDict(frozen=True)

    start: date
    end: date
    days: list[CalendarDay] = Field(default_factory=list)

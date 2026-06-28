from __future__ import annotations

from datetime import date
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class DealKind(StrEnum):
    """特売・ポイント施策の種別。"""

    POINT_DAY = "point_day"
    """ポイント還元・倍率アップ (例: WAON ポイント 5 倍)。"""
    DISCOUNT_DAY = "discount_day"
    """会計から割引 (例: お客様感謝デー 5% OFF)。"""
    BARGAIN = "bargain"
    """個別商品の特売 (チラシ品)。"""


class Deal(BaseModel):
    """ある店舗の、ある日付に有効な特売・ポイント施策。"""

    model_config = ConfigDict(frozen=True)

    store_id: str
    chain_id: str
    on: date
    kind: DealKind
    title: str = Field(min_length=1, description="例: お客様感謝デー")
    description: str = Field(default="")
    discount_percent: float | None = Field(
        default=None, ge=0.0, le=100.0, description="会計割引率 (%)"
    )
    point_multiplier: float | None = Field(
        default=None, ge=1.0, description="ポイント倍率 (例: 5.0 = 5 倍)"
    )

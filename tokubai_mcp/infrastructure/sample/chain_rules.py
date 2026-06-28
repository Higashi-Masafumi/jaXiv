from __future__ import annotations

from datetime import date, timedelta
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from domain.entities.deal import DealKind


class RuleType(StrEnum):
    MONTHLY_DAY = "monthly_day"
    """毎月の決まった日付 (例: 20 日・30 日)。"""
    WEEKDAY = "weekday"
    """毎週の決まった曜日 (月=0 〜 日=6)。"""


class DealRule(BaseModel):
    """チェーンの定期施策を表す規則。期間に展開して ``Deal`` を生成する。"""

    model_config = ConfigDict(frozen=True)

    kind: DealKind
    title: str
    description: str = ""
    discount_percent: float | None = None
    point_multiplier: float | None = None
    rule_type: RuleType
    values: tuple[int, ...] = Field(
        description="MONTHLY_DAY なら日付、WEEKDAY なら曜日 (月=0)"
    )

    def matches(self, d: date) -> bool:
        if self.rule_type is RuleType.MONTHLY_DAY:
            return d.day in self.values
        return d.weekday() in self.values


class ChainRules(BaseModel):
    """チェーン 1 つ分の定期施策の束。"""

    model_config = ConfigDict(frozen=True)

    chain_id: str
    display_name: str
    point_program: str = Field(default="", description="例: WAON POINT")
    rules: tuple[DealRule, ...]


def _daterange(start: date, end: date):
    cur = start
    while cur <= end:
        yield cur
        cur += timedelta(days=1)


# ---------------------------------------------------------------------------
# サンプルとして実在チェーンの代表的な定期施策を規則化したもの。
# 実データ (チラシ配信 API 等) に差し替える前提のイラストレーション用。
# 平日: 月=0, 火=1, 水=2, 木=3, 金=4, 土=5, 日=6
# ---------------------------------------------------------------------------
CHAIN_RULES: dict[str, ChainRules] = {
    "aeon": ChainRules(
        chain_id="aeon",
        display_name="イオン",
        point_program="WAON POINT",
        rules=(
            DealRule(
                kind=DealKind.DISCOUNT_DAY,
                title="お客様感謝デー",
                description="イオンカード・WAON のお支払いで 5% OFF",
                discount_percent=5.0,
                rule_type=RuleType.MONTHLY_DAY,
                values=(20, 30),
            ),
            DealRule(
                kind=DealKind.POINT_DAY,
                title="ありが10デー",
                description="WAON POINT が基本の 5 倍",
                point_multiplier=5.0,
                rule_type=RuleType.MONTHLY_DAY,
                values=(10,),
            ),
            DealRule(
                kind=DealKind.BARGAIN,
                title="火曜市",
                description="食品・日用品の週替わり特売",
                rule_type=RuleType.WEEKDAY,
                values=(1,),
            ),
        ),
    ),
    "ito-yokado": ChainRules(
        chain_id="ito-yokado",
        display_name="イトーヨーカドー",
        point_program="nanaco",
        rules=(
            DealRule(
                kind=DealKind.DISCOUNT_DAY,
                title="ハッピーデー",
                description="セブンカード・nanaco のお支払いで 5% OFF",
                discount_percent=5.0,
                rule_type=RuleType.MONTHLY_DAY,
                values=(8, 18, 28),
            ),
            DealRule(
                kind=DealKind.BARGAIN,
                title="日曜市",
                description="週末の目玉特売",
                rule_type=RuleType.WEEKDAY,
                values=(6,),
            ),
        ),
    ),
    "seiyu": ChainRules(
        chain_id="seiyu",
        display_name="西友",
        point_program="楽天ポイント",
        rules=(
            DealRule(
                kind=DealKind.BARGAIN,
                title="土日特売",
                description="週末限定のお買い得品",
                rule_type=RuleType.WEEKDAY,
                values=(5, 6),
            ),
            DealRule(
                kind=DealKind.POINT_DAY,
                title="楽天ポイント 2 倍デー",
                description="毎月 5 のつく日は楽天ポイント 2 倍",
                point_multiplier=2.0,
                rule_type=RuleType.MONTHLY_DAY,
                values=(5, 15, 25),
            ),
        ),
    ),
    "life": ChainRules(
        chain_id="life",
        display_name="ライフ",
        point_program="LC ポイント",
        rules=(
            DealRule(
                kind=DealKind.POINT_DAY,
                title="ポイント 5 倍デー",
                description="LC ポイントが 5 倍",
                point_multiplier=5.0,
                rule_type=RuleType.MONTHLY_DAY,
                values=(15, 25),
            ),
            DealRule(
                kind=DealKind.BARGAIN,
                title="木曜・金曜の生鮮特売",
                description="精肉・鮮魚・青果のまとめ買いセール",
                rule_type=RuleType.WEEKDAY,
                values=(3, 4),
            ),
        ),
    ),
    "gyomu-super": ChainRules(
        chain_id="gyomu-super",
        display_name="業務スーパー",
        point_program="",
        rules=(
            DealRule(
                kind=DealKind.BARGAIN,
                title="月初の業務用大特価",
                description="毎月 1〜3 日は冷凍・大容量商品が特価",
                rule_type=RuleType.MONTHLY_DAY,
                values=(1, 2, 3),
            ),
        ),
    ),
}


def known_chain_ids() -> list[str]:
    return sorted(CHAIN_RULES.keys())

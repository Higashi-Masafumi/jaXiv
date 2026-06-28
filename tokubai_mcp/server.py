"""特売・ポイントデー情報を提供する MCP サーバー (tokubai-mcp)。

近くのスーパーを登録すると、チェーンごとのポイントデー・割引デー・特売を
カレンダーとして取得でき、最もお得な買い物日を提案する。

起動 (stdio):
    uv run python server.py
"""

from __future__ import annotations

import logging
from datetime import date

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, ConfigDict

from dependencies import (
    get_build_calendar_use_case,
    get_find_best_day_use_case,
    get_register_store_use_case,
    get_search_stores_use_case,
    get_store_repository,
)
from domain.entities.calendar import DealCalendar
from domain.entities.deal import Deal, DealKind
from domain.entities.store import NearbyStore, Store
from domain.errors.errors import TokubaiError
from infrastructure.sample.chain_rules import CHAIN_RULES
from usecase.find_best_day import DayScore
from usecase.register_store import RegisterStoreIn

logging.basicConfig(level=logging.INFO)

mcp = FastMCP(
    "tokubai",
    instructions=(
        "近くのスーパーの特売・ポイントデー情報サーバー。"
        "search_nearby_stores で店舗を探し register_store で登録、"
        "get_deal_calendar でカレンダーを取得、"
        "find_best_shopping_day で最もお得な買い物日を提案します。"
    ),
)


class ChainInfo(BaseModel):
    model_config = ConfigDict(frozen=True)

    chain_id: str
    display_name: str
    point_program: str


@mcp.tool()
def list_supported_chains() -> list[ChainInfo]:
    """対応しているスーパーチェーン (ポイントデー規則を持つ) の一覧を返す。"""
    return [
        ChainInfo(
            chain_id=c.chain_id,
            display_name=c.display_name,
            point_program=c.point_program,
        )
        for c in CHAIN_RULES.values()
    ]


@mcp.tool()
def search_nearby_stores(
    latitude: float,
    longitude: float,
    radius_km: float = 3.0,
    limit: int = 20,
) -> list[NearbyStore]:
    """緯度・経度を基準に近隣のスーパー候補を距離(km)昇順で返す。"""
    return get_search_stores_use_case().execute(
        latitude=latitude, longitude=longitude, radius_km=radius_km, limit=limit
    )


@mcp.tool()
def register_store(
    id: str,
    name: str,
    chain_id: str,
    latitude: float,
    longitude: float,
    address: str = "",
) -> Store:
    """近くのスーパーを登録する。chain_id は list_supported_chains の値を使う。"""
    try:
        return get_register_store_use_case().execute(
            RegisterStoreIn(
                id=id,
                name=name,
                chain_id=chain_id,
                latitude=latitude,
                longitude=longitude,
                address=address,
            )
        )
    except TokubaiError as e:
        raise ValueError(str(e)) from e


@mcp.tool()
def list_registered_stores() -> list[Store]:
    """登録済みの店舗一覧を返す。"""
    return get_store_repository().list_all()


@mcp.tool()
def unregister_store(store_id: str) -> dict[str, bool]:
    """登録済みの店舗を解除する。"""
    removed = get_store_repository().remove(store_id)
    return {"removed": removed}


@mcp.tool()
def get_deal_calendar(
    start: date,
    end: date,
    store_ids: list[str] | None = None,
) -> DealCalendar:
    """期間 [start, end] の特売カレンダーを返す。

    store_ids 省略時は登録済みの全店舗が対象。特売がある日のみを含む。
    """
    try:
        return get_build_calendar_use_case().execute(
            start=start, end=end, store_ids=store_ids
        )
    except TokubaiError as e:
        raise ValueError(str(e)) from e


@mcp.tool()
def get_point_days(
    store_id: str,
    start: date,
    end: date,
) -> list[Deal]:
    """指定店舗の、期間内のポイントデー (ポイント倍率アップ) だけを返す。"""
    try:
        calendar = get_build_calendar_use_case().execute(
            start=start, end=end, store_ids=[store_id]
        )
    except TokubaiError as e:
        raise ValueError(str(e)) from e
    return [
        deal
        for day in calendar.days
        for deal in day.deals
        if deal.kind is DealKind.POINT_DAY
    ]


@mcp.tool()
def find_best_shopping_day(
    start: date,
    end: date,
    store_ids: list[str] | None = None,
    limit: int = 5,
) -> list[DayScore]:
    """期間内で最もお得な買い物日を実効割引率の高い順にランキングして返す。"""
    try:
        return get_find_best_day_use_case().execute(
            start=start, end=end, store_ids=store_ids, limit=limit
        )
    except TokubaiError as e:
        raise ValueError(str(e)) from e


if __name__ == "__main__":
    mcp.run()

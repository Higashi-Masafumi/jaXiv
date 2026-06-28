from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from domain.entities.geo import GeoPoint


class Store(BaseModel):
    """ユーザーが登録した、あるいは近隣で見つかったスーパーの店舗。"""

    model_config = ConfigDict(frozen=True)

    id: str
    name: str = Field(min_length=1)
    chain_id: str = Field(
        description="ポイントデー規則を解決するためのチェーン識別子 (例: aeon)"
    )
    address: str = Field(default="")
    location: GeoPoint


class NearbyStore(BaseModel):
    """検索結果。基準地点からの距離 (km) を付与した店舗。"""

    model_config = ConfigDict(frozen=True)

    store: Store
    distance_km: float = Field(ge=0.0)

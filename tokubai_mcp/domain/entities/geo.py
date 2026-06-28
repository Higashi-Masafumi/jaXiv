from __future__ import annotations

import math

from pydantic import BaseModel, ConfigDict, Field

EARTH_RADIUS_KM = 6371.0088


class GeoPoint(BaseModel):
    """緯度・経度の値オブジェクト。"""

    model_config = ConfigDict(frozen=True)

    latitude: float = Field(ge=-90.0, le=90.0)
    longitude: float = Field(ge=-180.0, le=180.0)

    def distance_km(self, other: GeoPoint) -> float:
        """2 点間の大円距離 (km) を haversine で計算する。"""
        lat1, lon1 = math.radians(self.latitude), math.radians(self.longitude)
        lat2, lon2 = math.radians(other.latitude), math.radians(other.longitude)
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        )
        return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))

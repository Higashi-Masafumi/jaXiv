from __future__ import annotations

from domain.entities.geo import GeoPoint
from domain.entities.store import NearbyStore
from domain.gateways.store_repository import StoreRepository


class SearchStoresUseCase:
    """基準地点の近隣スーパーを距離昇順で探す。"""

    def __init__(self, repository: StoreRepository) -> None:
        self._repository = repository

    def execute(
        self,
        latitude: float,
        longitude: float,
        radius_km: float = 3.0,
        limit: int = 20,
    ) -> list[NearbyStore]:
        origin = GeoPoint(latitude=latitude, longitude=longitude)
        return self._repository.search_nearby(origin, radius_km, limit)

from __future__ import annotations

from abc import ABC, abstractmethod

from domain.entities.geo import GeoPoint
from domain.entities.store import NearbyStore, Store


class StoreRepository(ABC):
    """ユーザーが登録した店舗の永続化ポート。"""

    @abstractmethod
    def add(self, store: Store) -> None:
        """店舗を登録する (同一 id は上書き)。"""
        raise NotImplementedError

    @abstractmethod
    def get(self, store_id: str) -> Store | None:
        raise NotImplementedError

    @abstractmethod
    def list_all(self) -> list[Store]:
        raise NotImplementedError

    @abstractmethod
    def remove(self, store_id: str) -> bool:
        """登録解除する。存在すれば True。"""
        raise NotImplementedError

    @abstractmethod
    def search_nearby(
        self, origin: GeoPoint, radius_km: float, limit: int
    ) -> list[NearbyStore]:
        """近隣の候補店舗を距離昇順で返す (まだ登録していない店舗を含む)。"""
        raise NotImplementedError

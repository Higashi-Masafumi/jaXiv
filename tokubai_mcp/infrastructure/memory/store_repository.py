from __future__ import annotations

from collections.abc import Iterable

from domain.entities.geo import GeoPoint
from domain.entities.store import NearbyStore, Store
from domain.gateways.store_repository import StoreRepository


class InMemoryStoreRepository(StoreRepository):
    """プロセス内メモリで登録店舗を保持する実装。

    ``catalog`` は近隣検索の候補 (未登録の実在店舗) として用いる。
    本番では永続 DB + ジオ検索に差し替える。
    """

    def __init__(self, catalog: Iterable[Store] = ()) -> None:
        self._stores: dict[str, Store] = {}
        self._catalog: list[Store] = list(catalog)

    def add(self, store: Store) -> None:
        self._stores[store.id] = store

    def get(self, store_id: str) -> Store | None:
        return self._stores.get(store_id)

    def list_all(self) -> list[Store]:
        return list(self._stores.values())

    def remove(self, store_id: str) -> bool:
        return self._stores.pop(store_id, None) is not None

    def search_nearby(
        self, origin: GeoPoint, radius_km: float, limit: int
    ) -> list[NearbyStore]:
        # 登録済み + カタログを統合し、id 重複は登録済みを優先する。
        merged: dict[str, Store] = {s.id: s for s in self._catalog}
        merged.update({s.id: s for s in self._stores.values()})

        within = [
            NearbyStore(store=s, distance_km=origin.distance_km(s.location))
            for s in merged.values()
        ]
        within = [n for n in within if n.distance_km <= radius_km]
        within.sort(key=lambda n: n.distance_km)
        return within[:limit]

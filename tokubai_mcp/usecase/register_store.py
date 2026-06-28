from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from domain.entities.geo import GeoPoint
from domain.entities.store import Store
from domain.errors.errors import UnknownChainError
from domain.gateways.store_repository import StoreRepository
from infrastructure.sample.chain_rules import CHAIN_RULES


class RegisterStoreIn(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    chain_id: str = Field(min_length=1)
    latitude: float
    longitude: float
    address: str = ""


class RegisterStoreUseCase:
    """ユーザーが近くのスーパーを登録する。"""

    def __init__(self, repository: StoreRepository) -> None:
        self._repository = repository

    def execute(self, data: RegisterStoreIn) -> Store:
        if data.chain_id not in CHAIN_RULES:
            raise UnknownChainError(data.chain_id)
        store = Store(
            id=data.id,
            name=data.name,
            chain_id=data.chain_id,
            address=data.address,
            location=GeoPoint(latitude=data.latitude, longitude=data.longitude),
        )
        self._repository.add(store)
        return store

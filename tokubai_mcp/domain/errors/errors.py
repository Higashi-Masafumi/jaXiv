from __future__ import annotations


class TokubaiError(Exception):
    """このサービス共通の基底エラー。"""


class StoreNotFoundError(TokubaiError):
    def __init__(self, store_id: str) -> None:
        super().__init__(f"店舗が見つかりません: {store_id}")
        self.store_id = store_id


class UnknownChainError(TokubaiError):
    def __init__(self, chain_id: str) -> None:
        super().__init__(f"未知のチェーンです: {chain_id}")
        self.chain_id = chain_id

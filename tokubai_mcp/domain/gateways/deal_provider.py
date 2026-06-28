from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date

from domain.entities.deal import Deal
from domain.entities.store import Store


class DealProvider(ABC):
    """特売・ポイント施策の供給ポート。

    サンプル実装はチェーンごとの規則 (ポイントデー等) からデータを生成するが、
    本番ではチラシ配信 API やスクレイピング結果に差し替えられる。
    """

    @abstractmethod
    def deals_for(self, store: Store, start: date, end: date) -> list[Deal]:
        """``start``〜``end`` (両端含む) の期間に有効な施策を返す。"""
        raise NotImplementedError

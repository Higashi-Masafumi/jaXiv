from __future__ import annotations

from datetime import date

from domain.entities.deal import Deal
from domain.entities.store import Store
from domain.gateways.deal_provider import DealProvider
from infrastructure.sample.chain_rules import CHAIN_RULES, _daterange


class RuleBasedDealProvider(DealProvider):
    """チェーンの定期施策ルールを期間に展開して特売を生成するサンプル実装。

    チラシをスクレイプせずとも、ポイントデー・割引デーなど規則的な施策は
    任意の月について算出できる。未知のチェーンは施策なしとして扱う。
    """

    def deals_for(self, store: Store, start: date, end: date) -> list[Deal]:
        chain = CHAIN_RULES.get(store.chain_id)
        if chain is None:
            return []

        deals: list[Deal] = []
        for d in _daterange(start, end):
            for rule in chain.rules:
                if not rule.matches(d):
                    continue
                deals.append(
                    Deal(
                        store_id=store.id,
                        chain_id=store.chain_id,
                        on=d,
                        kind=rule.kind,
                        title=rule.title,
                        description=rule.description,
                        discount_percent=rule.discount_percent,
                        point_multiplier=rule.point_multiplier,
                    )
                )
        return deals

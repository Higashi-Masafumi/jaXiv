from __future__ import annotations

from domain.entities.geo import GeoPoint
from domain.entities.store import Store

# 近隣検索のためのサンプル店舗カタログ (東京近郊)。
# 実運用ではジオコーディング API / 店舗マスタに置き換える。
SAMPLE_STORE_CATALOG: tuple[Store, ...] = (
    Store(
        id="aeon-shinagawa",
        name="イオン 品川シーサイド店",
        chain_id="aeon",
        address="東京都品川区東品川4-12-5",
        location=GeoPoint(latitude=35.6092, longitude=139.7503),
    ),
    Store(
        id="ito-yokado-omori",
        name="イトーヨーカドー 大森店",
        chain_id="ito-yokado",
        address="東京都大田区大森北2-13-1",
        location=GeoPoint(latitude=35.5879, longitude=139.7281),
    ),
    Store(
        id="seiyu-osaki",
        name="西友 大崎店",
        chain_id="seiyu",
        address="東京都品川区大崎1-2-2",
        location=GeoPoint(latitude=35.6197, longitude=139.7286),
    ),
    Store(
        id="life-gotanda",
        name="ライフ 五反田店",
        chain_id="life",
        address="東京都品川区東五反田1-13-12",
        location=GeoPoint(latitude=35.6266, longitude=139.7237),
    ),
    Store(
        id="gyomu-super-meguro",
        name="業務スーパー 目黒店",
        chain_id="gyomu-super",
        address="東京都目黒区目黒1-4-1",
        location=GeoPoint(latitude=35.6332, longitude=139.7156),
    ),
    Store(
        id="aeon-shibuya",
        name="イオンスタイル 渋谷",
        chain_id="aeon",
        address="東京都渋谷区宇田川町23-3",
        location=GeoPoint(latitude=35.6615, longitude=139.6983),
    ),
)

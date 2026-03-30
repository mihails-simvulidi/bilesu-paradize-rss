from datetime import datetime
from typing import Any

from app import (
    DEFAULT_LANG,
    availability_label,
    build_feed_items,
    build_source_url,
    format_feed_date,
    resource_title,
)


SAMPLE_EVENTS: list[dict[str, Any]] = [
    {
        "id": 166589,
        "performance_titles": {
            "lv": "Labdarības koncerts “Ja skatuves dēļi sāktu runāt”",
            "en": "Benefit concert",
        },
        "city": "Rīga",
        "date_time": "2026-03-30 19:00:00",
        "price_groups": [{"count": 3}, {"count": 0}],
    },
    {
        "id": 164920,
        "performance_titles": {
            "lv": "Viss par Ievu",
            "en": "All About Eve",
        },
        "city": "Rīga",
        "date_time": "2026-03-31 19:00:00",
        "price_groups": [{"count": 0}, {"count": 0}],
    },
]

def test_build_feed_items_extracts_event_link_and_title() -> None:
    items = build_feed_items(SAMPLE_EVENTS)

    assert [item.link for item in items] == [
        "https://www.bilesuparadize.lv/lv/event/166589",
        "https://www.bilesuparadize.lv/lv/event/164920",
    ]
    assert (
        items[0].title
        == "Labdarības koncerts “Ja skatuves dēļi sāktu runāt” - pirmdien, 2026. gada 30. martā - Rīga - pārdošanā"
    )
    assert items[1].title == "Viss par Ievu - otrdien, 2026. gada 31. martā - Rīga - izpārdots"


def test_format_feed_date_for_latvian() -> None:
    value = datetime(2026, 4, 1, 19, 0)
    assert format_feed_date(value) == "trešdien, 2026. gada 1. aprīlī"


def test_availability_label_for_latvian() -> None:
    assert availability_label({"price_groups": [{"count": 1}]}) == "pārdošanā"
    assert availability_label({"price_groups": [{"count": 0}]}) == "izpārdots"


def test_build_source_url_supports_performance() -> None:
    assert build_source_url("location", 38) == (
        "https://www.bilesuparadize.lv/lv/location/38?page=1&showOnlyAvailable=true"
    )
    assert build_source_url("performance", 33206) == (
        "https://www.bilesuparadize.lv/lv/performance/33206?page=1&showOnlyAvailable=true"
    )


def test_resource_title_prefers_lv_translation_and_falls_back_to_title() -> None:
    assert resource_title({"title_translations": {DEFAULT_LANG: "NACIONĀLAIS TEĀTRIS"}}) == (
        "NACIONĀLAIS TEĀTRIS"
    )
    assert resource_title({"title": "Ilgu tramvajs"}) == "Ilgu tramvajs"
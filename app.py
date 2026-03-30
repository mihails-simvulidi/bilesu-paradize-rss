from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from email.utils import format_datetime
from typing import Any
from xml.etree import ElementTree as ET
from zoneinfo import ZoneInfo

from curl_cffi import requests as curl_requests
from flask import Flask, Response

BASE_URL = "https://www.bilesuparadize.lv"
API_BASE_URL = f"{BASE_URL}/api"
LATVIAN_TIMEZONE = ZoneInfo("Europe/Riga")
REQUEST_TIMEOUT = 30
RSS_DESCRIPTION = "RSS feed generated from bilesuparadize.lv"
SHOW_ONLY_AVAILABLE = "true"
DEFAULT_LANG = "lv"
SUPPORTED_RESOURCE_TYPES = {"location", "performance"}
USER_AGENT = (
    "bilesu-paradize-rss/1.0 "
    "(+https://github.com/mihails-simvulidi/bilesu-paradize-rss)"
)
WEEKDAY_NAMES = [
    "pirmdien",
    "otrdien",
    "trešdien",
    "ceturtdien",
    "piektdien",
    "sestdien",
    "svētdien",
]
MONTH_NAMES = [
    "janvārī",
    "februārī",
    "martā",
    "aprīlī",
    "maijā",
    "jūnijā",
    "jūlijā",
    "augustā",
    "septembrī",
    "oktobrī",
    "novembrī",
    "decembrī",
]

app = Flask(__name__)


@dataclass(frozen=True)
class FeedItem:
    title: str
    link: str
    guid: str
    published_at: datetime | None = None


def build_http_session() -> Any:
    return curl_requests.Session(impersonate="chrome")


def build_source_url(resource_type: str, resource_id: int) -> str:
    return (
        f"{BASE_URL}/{DEFAULT_LANG}/{resource_type}/{resource_id}"
        f"?page=1&showOnlyAvailable={SHOW_ONLY_AVAILABLE}"
    )


def build_resource_api_url(resource_type: str, resource_id: int) -> str:
    resource_name = "venue" if resource_type == "location" else resource_type
    return f"{API_BASE_URL}/{resource_name}/{resource_id}"


def build_events_api_url(resource_type: str, resource_id: int) -> str:
    resource_name = "venue" if resource_type == "location" else resource_type
    return f"{API_BASE_URL}/{resource_name}/{resource_id}/event?showOnlyAvailable={SHOW_ONLY_AVAILABLE}"


def parse_upstream_datetime(raw_value: str | None) -> datetime | None:
    if not raw_value:
        return None

    try:
        return datetime.strptime(raw_value, "%Y-%m-%d %H:%M:%S").replace(
            tzinfo=LATVIAN_TIMEZONE
        )
    except ValueError:
        return None


def format_feed_date(value: datetime) -> str:
    return (
        f"{WEEKDAY_NAMES[value.weekday()]}, "
        f"{value.year}. gada {value.day}. {MONTH_NAMES[value.month - 1]}"
    )


def availability_label(event: dict[str, Any]) -> str:
    price_groups = event.get("price_groups") or []
    has_available_tickets = any(
        isinstance(group, dict) and isinstance(group.get("count"), (int, float)) and group["count"] > 0
        for group in price_groups
    )

    return "pārdošanā" if has_available_tickets else "izpārdots"


def fetch_json(session: Any, url: str) -> Any:
    response = session.get(
        url,
        headers={"Accept": "application/json", "User-Agent": USER_AGENT},
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


def resource_title(resource: dict[str, Any]) -> str:
    translations = resource.get("title_translations")
    if isinstance(translations, dict):
        lv_title = translations.get(DEFAULT_LANG)
        if isinstance(lv_title, str) and lv_title.strip():
            return lv_title.strip()

    fallback_title = resource.get("title")
    if isinstance(fallback_title, str) and fallback_title.strip():
        return fallback_title.strip()

    return "Biļešu Paradīze"


def build_feed_items(events: list[dict[str, Any]]) -> list[FeedItem]:
    items: list[FeedItem] = []
    seen_links: set[str] = set()

    for event in sorted(
        events,
        key=lambda item: (
            parse_upstream_datetime(item.get("date_time")) or datetime.max.replace(tzinfo=LATVIAN_TIMEZONE),
            int(item.get("id", 0)),
        ),
    ):
        event_id = event.get("id")
        if not isinstance(event_id, int):
            continue

        link = f"{BASE_URL}/{DEFAULT_LANG}/event/{event_id}"
        if link in seen_links:
            continue

        performance_titles = event.get("performance_titles")
        if not isinstance(performance_titles, dict):
            continue

        title = performance_titles.get(DEFAULT_LANG)
        if isinstance(title, str):
            title = title.strip()
        if not title:
            continue

        published_at = parse_upstream_datetime(event.get("date_time"))
        city = event.get("city")
        city_text = city.strip() if isinstance(city, str) else ""
        item_title = f"{title} - {availability_label(event)}"
        if published_at is not None:
            date_part = f"{title} - {format_feed_date(published_at)}"
            if city_text:
                item_title = f"{date_part} - {city_text} - {availability_label(event)}"
            else:
                item_title = f"{date_part} - {availability_label(event)}"

        seen_links.add(link)
        items.append(FeedItem(title=item_title, link=link, guid=link, published_at=published_at))

    return items


def build_feed(resource_type: str, resource_id: int) -> tuple[str, str, list[FeedItem]]:
    session = build_http_session()
    resource = fetch_json(session, build_resource_api_url(resource_type, resource_id))
    events = fetch_json(session, build_events_api_url(resource_type, resource_id))

    if not isinstance(resource, dict):
        raise ValueError("Unexpected resource response format")
    if not isinstance(events, list):
        raise ValueError("Unexpected event response format")

    return (
        resource_title(resource),
        build_source_url(resource_type, resource_id),
        build_feed_items(events),
    )


def rss_xml(feed_title: str, feed_link: str, items: list[FeedItem]) -> str:
    rss = ET.Element("rss", attrib={"version": "2.0"})
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = feed_title
    ET.SubElement(channel, "description").text = RSS_DESCRIPTION
    ET.SubElement(channel, "link").text = feed_link

    for feed_item in items:
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "guid").text = feed_item.guid
        ET.SubElement(item, "link").text = feed_item.link
        ET.SubElement(item, "title").text = feed_item.title
        if feed_item.published_at is not None:
            ET.SubElement(item, "pubDate").text = format_datetime(feed_item.published_at)

    ET.indent(rss, space="  ")
    xml_bytes = ET.tostring(rss, encoding="utf-8", xml_declaration=True)
    return f"{xml_bytes.decode('utf-8')}\n"


@app.route("/")
def home() -> Response:
    return Response(
        "Use /<location|performance>/<id> to get an RSS feed, e.g. /location/38 or /performance/33206\n",
        mimetype="text/plain",
    )


@app.route("/<resource_type>/<int:resource_id>")
def rss_proxy(resource_type: str, resource_id: int) -> Response:
    if resource_type not in SUPPORTED_RESOURCE_TYPES:
        return Response("Unsupported resource type\n", status=404, mimetype="text/plain")

    try:
        feed_title, source_url, items = build_feed(resource_type, resource_id)
    except Exception as exc:
        return Response(f"Upstream fetch failed: {exc}\n", status=502, mimetype="text/plain")

    xml = rss_xml(feed_title, source_url, items)
    return Response(xml, mimetype="application/rss+xml; charset=utf-8")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)

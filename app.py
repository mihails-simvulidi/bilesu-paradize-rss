from bs4 import BeautifulSoup, Tag
from flask import Flask, Response
from urllib.parse import urljoin, urlparse
from xml.etree import ElementTree as ET
import requests

BASE_URL = "https://www.bilesuparadize.lv"
BASE_HOST = urlparse(BASE_URL).netloc
REQUEST_TIMEOUT = (3.05, 10)
USER_AGENT = "bilesu-paradize-rss/1.0 (+https://github.com/mihails-simvulidi/bilesu-paradize-rss)"

app = Flask(__name__)


@app.route("/")
def home():
    return Response(
        "Use /<lang>/<category>/<id> to get RSS feed, e.g. /lv/performance/12345\n",
        mimetype="text/plain",
    )


@app.route("/<path:path>")
def rss_proxy(path: str):

    # Fetch the source page
    source_url = f"{BASE_URL}/{path}"
    response = requests.get(
        source_url,
        headers={"User-Agent": USER_AGENT},
    )
    response.raise_for_status()

    # Set channel attributes
    soup = BeautifulSoup(response.text, "html.parser")
    rss = ET.Element("rss", attrib={"version": "2.0"})
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(
        channel, "description"
    ).text = "https://github.com/mihails-simvulidi/bilesu-paradize-rss"
    ET.SubElement(channel, "link").text = source_url
    title_element = soup.find("title")
    if isinstance(title_element, Tag):
        ET.SubElement(channel, "title").text = title_element.text

    # Extract event items
    event_elements = soup.find_all("div", attrs={"role": "listitem"})
    for event_element in event_elements:
        date_link = event_element.find("a", class_="scoped-date")
        item = ET.SubElement(channel, "item")
        event_name = event_element.find("span", class_="md:text-lg").text
        event_url = urljoin(BASE_URL, date_link["href"])
        event_status = event_element.find("a", class_="button").text
        ET.SubElement(item, "guid").text = event_url
        ET.SubElement(item, "link").text = event_url
        ET.SubElement(
            item, "title"
        ).text = f"{event_name} {date_link.text} {event_status}"

    # Return the RSS feed as XML
    ET.indent(rss, space="  ")
    xml_bytes = ET.tostring(rss, encoding="utf-8", xml_declaration=True)
    rss_string = f"{xml_bytes.decode('utf-8')}\n"
    return Response(rss_string, mimetype="application/rss+xml; charset=utf-8")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)

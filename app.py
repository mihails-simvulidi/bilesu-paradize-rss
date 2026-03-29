from bs4 import BeautifulSoup, Tag
from fake_useragent import UserAgent
from flask import Flask, Response
from urllib.parse import urljoin
from xml.etree import ElementTree as ET
import requests

BASE_URL = "https://www.bilesuparadize.lv"

app = Flask(__name__)


@app.route("/")
def home():
    return Response(
        "Use /<lang>/<category>/<id> to get RSS feed, e.g. /lv/performance/12345\n",
        mimetype="text/plain",
    )


@app.route("/<path:path>")
def rss_proxy(path: str):
    user_agent = UserAgent()
    source_url = urljoin(BASE_URL, path)
    response = requests.get(source_url, headers={"User-Agent": user_agent.random})
    response.raise_for_status()
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
    event_elements = soup.find_all("div", attrs={"role": "listitem"})
    for event_element in event_elements:
        link_element = event_element.find("a", class_="scoped-date")
        item = ET.SubElement(channel, "item")
        event_url = urljoin(BASE_URL, link_element["href"])
        ET.SubElement(item, "guid").text = event_url
        ET.SubElement(item, "link").text = event_url
        ET.SubElement(item, "title").text = link_element.text
    ET.indent(rss, space="  ")
    xml_bytes = ET.tostring(rss, encoding="utf-8", xml_declaration=True)
    rss_string = f"{xml_bytes.decode('utf-8')}\n"
    return Response(rss_string, mimetype="application/rss+xml; charset=utf-8")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)

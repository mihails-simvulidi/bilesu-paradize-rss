# bilesu-paradize-rss

A small AI generated Python Flask service that converts location and performance listings from bilesuparadize.lv into an RSS 2.0 feed.

## What it does

- Accepts a path like `/location/38` or `/performance/33206`
- Always uses Latvian (`lv`) upstream data and link paths
- Uses the upstream venue JSON API behind `https://www.bilesuparadize.lv/lv/location/38?page=1&showOnlyAvailable=true`
- Includes all currently available events for the venue in one feed
- Generates an RSS feed where the channel title comes from the venue page and items point to the individual event pages

## Endpoints

- `GET /`
  - Plain-text usage hint
- `GET /location/<id>`
- `GET /performance/<id>`
  - Returns RSS XML (`application/rss+xml; charset=utf-8`)

Example:

```bash
curl http://localhost/location/38
```

## Local development

### Requirements

- Python 3.11+
- pip

### Install dependencies

```bash
pip install -r requirements.txt
```

### Run locally

```bash
python app.py
```

### Run with Gunicorn

```bash
gunicorn --bind 0.0.0.0:80 app:app
```

## Docker

### Build image

```bash
docker build -t bilesu-paradize-rss .
```

### Run container

```bash
docker run --rm -p 80:80 bilesu-paradize-rss
```

Then open `http://localhost:80/location/38`.

## Notes

- The upstream site is protected by Cloudflare; this service uses `curl_cffi` with browser impersonation and the venue JSON API instead of scraping rendered HTML.
- Event titles are built from the upstream event payload and formatted as a single Latvian title line with date and availability status.
- If the upstream markup or anti-bot protection changes, the parser may need to be adjusted.

# bilesu-paradize-rss

A small Flask service that converts pages from [bilesuparadize.lv](https://www.bilesuparadize.lv) into an RSS 2.0 feed.

## What it does

- Accepts a path like `/lv/performance/12345`
- Fetches the corresponding page from `https://www.bilesuparadize.lv`
- Parses event entries from HTML (`div[role="listitem"]`)
- Returns an RSS XML document with event links and titles

## Endpoints

- `GET /`
  - Plain-text usage hint
- `GET /<lang>/<category>/<id>` (implemented as `GET /<path:path>`)
  - Returns RSS XML (`application/rss+xml; charset=utf-8`)

Example:

```bash
curl http://localhost:8080/lv/performance/12345
```

## Local development

### Requirements

- Python 3.11+
- pip

### Install dependencies

```bash
pip install -r requirements.txt
```

### Run with Flask (development)

```bash
python app.py
```

The app listens on port `80` in this mode.

### Run with Gunicorn (production-like)

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
docker run --rm -p 8080:80 bilesu-paradize-rss
```

Then open:

- `http://localhost:8080/`
- `http://localhost:8080/lv/performance/12345`

## CI/CD

GitHub Actions workflow at `.github/workflows/docker-publish.yml` builds the Docker image on push and pull requests, and publishes to GHCR on non-PR events.

Registry/image naming is based on:

- `ghcr.io/<owner>/<repo>`

## Notes and limitations

- RSS items currently include `guid`, `link`, and `title`.
- The feed does not include `pubDate` or full descriptions.
- Output depends on the current HTML structure of bilesuparadize.lv.
- If upstream markup changes, parser updates may be required.

## License

MIT. See [LICENSE](LICENSE).

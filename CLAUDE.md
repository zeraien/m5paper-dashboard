# m5paper-dashboard

Renders the dashboard image for an M5Paper (ESP32, e-ink) on the home LAN. Replaces the former
Home Assistant dashboard + `sibbl/hass-lovelace-kindle-screensaver` pipeline: this service renders
its own HTML and serves the PNG directly.

Monorepo: `web/` is the server (Flask + Playwright, Docker), `uiflow/main.py` is the device code.
Public on GitHub as `zeraien/m5paper-dashboard`; the image is published to
`ghcr.io/zeraien/m5paper-dashboard` by `.github/workflows/docker.yml`.

## Standing directives
- Do not `git add` or `git commit` after implementation. The user reviews the working tree first.
- Responses use the TNG shipboard-computer register: declarative, impersonal, digits for numbers.
- Local-only application: CDN dependencies (Bootstrap, bootstrap-icons) are fine; network calls and
  render performance are not concerns. Do not change the web layout unless asked.

## Device contract (`uiflow/main.py`, UIFlow MicroPython on the M5Paper)
- Wakes hourly, `GET http://10.0.3.253:5000/`, writes the body to flash, displays it, sleeps 60 min.
- Reads `headers['Content-Length']` unconditionally: responses must never be streamed/chunked.
- Expects PNG, portrait 540×960, 16-level grayscale.
- Draws a battery label over the bottom-left corner at (0, 936), about 80×24 px.
- On a non-200 response the device keeps its boot image (`res/img/default.png`).

## Layout (paths under `web/`)
| Path | Role |
|---|---|
| `app.py` | Flask routes only. `/` renders `SCREEN_URL` (`/dashboard`) to PNG (503 text/plain on any failure, no cached image). `/dashboard` combines weather + calendar; `/weather` and `/calendar` are single-section preview pages. |
| `einkdisplay/forecast.py` | met.no data: `dl_forecast()`, `build_forecasts()`, `Forecast` (6-hour blocks, feels-like shows `?` when not computable). |
| `einkdisplay/renderer.py` | `render_png(url, width, height)`: headless Chromium (Playwright) screenshot → grayscale, contrast ×2, 16 levels. Knows nothing about page content. |
| `einkdisplay/calendar.py` | Google Calendar ICS: `dl_calendar()`, `build_days()` → `CalendarDay` (today, tomorrow) of `CalendarEvent`; recurrences expanded, cancelled and finished events dropped. With `max_rows`, rows are capped (overflow titles in `hidden_events`, one row) and Tomorrow is dropped unless Today has fewer events than the cap. |
| `einkdisplay/weather_symbols.py` | met.no symbol name → `static/symbols/<code>.svg`. |
| `templates/` | Jinja templates (Bootstrap 5 from CDN). Sections live in partials (`_weather.html`, `_calendar.html`, each self-contained incl. its `<style>`); `dashboard.html`, `weather.html`, `calendar.html` extend `_base.html` and `{% include %}` them. |

## Configuration
`settings.env` (git-ignored, copy from `settings.env.example`): `YR_IDENTITY`, `WEATHER_LAT`,
`WEATHER_LON`, `TZ`, `SCREEN_WIDTH`, `SCREEN_HEIGHT`, `CALENDAR_ICS` (all required), and
`CALENDAR_MAX_ROWS` (optional, default 6: optional so existing deployments keep starting).

## Run and test (from `web/`)
- `docker compose up --build` serves on port 5000 (gunicorn, 1 worker, 4 threads; threads are
  required because `/` makes Chromium request `/dashboard` from the same process).
- Tests need Chromium, so run them in the container with the source mounted:
  `docker compose run --rm -v "$PWD:/python-docker" app pytest`
- The user may run a local `flask run --debug` on `127.0.0.1:5000` from WSL, which shadows the
  container's port on localhost. Check the container from inside:
  `docker compose exec app python -c "import urllib.request; ..."`.

## CI and deployment
- Push to `main` touching `web/**` (or a `v*` tag): CI builds `./web`, runs `pytest` in the image
  (linux/amd64), then pushes a linux/amd64 + linux/arm64 image tagged `latest`, `sha-<short>`
  and semver tags.
- Server: `web/docker-compose.yaml` + `settings.env`, then `docker compose pull && docker compose up -d`.
- `web/.dockerignore` keeps `settings.env` (secret ICS URL) out of locally built images.
- Never commit `settings.env`, `*.sync-conflict-*` files (Syncthing) or exact home coordinates;
  test fixtures use Oslo coordinates.

"""
Render the dashboard from the test fixtures (no real forecast or calendar data) to a PNG,
e.g. for the README screenshot. Run from web/:

    docker compose run --rm -v "$PWD:/python-docker" -v "$PWD/../docs:/out" \
        app python tools/readme_screenshot.py /out/screenshot.png
"""
import json
import os
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

WEB_DIR = Path(__file__).resolve().parents[1]
FIXTURES = WEB_DIR / 'tests' / 'fixtures'

os.environ['TZ'] = 'Europe/Brussels'
time.tzset()
for key, value in {'YR_IDENTITY': 'screenshot', 'WEATHER_LAT': '59.91', 'WEATHER_LON': '10.75',
                   'SCREEN_WIDTH': '540', 'SCREEN_HEIGHT': '960',
                   'CALENDAR_ICS': 'http://calendar.invalid/basic.ics'}.items():
    os.environ.setdefault(key, value)
sys.path.insert(0, str(WEB_DIR))

from werkzeug.serving import make_server  # noqa: E402

import app as app_module  # noqa: E402
from einkdisplay.renderer import render_png  # noqa: E402

NOW = datetime(2025, 4, 2, 11, 30).astimezone()
PORT = 5055


class FixedDatetime(datetime):
    @classmethod
    def now(cls, tz=None):
        return NOW


def main(output: Path):
    app_module.datetime = FixedDatetime
    app_module.dl_forecast = lambda **kwargs: json.loads(
        (FIXTURES / 'locationforecast_sample.json').read_text())
    app_module.dl_calendar = lambda url: (FIXTURES / 'calendar.ics').read_bytes()

    server = make_server('127.0.0.1', PORT, app_module.app, threaded=True)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        png = render_png(f'http://127.0.0.1:{PORT}/dashboard',
                         width=app_module.SCREEN_WIDTH, height=app_module.SCREEN_HEIGHT)
    finally:
        server.shutdown()

    output.write_bytes(png)
    print(f"Wrote {output} ({len(png)} bytes)")


if __name__ == '__main__':
    main(Path(sys.argv[1] if len(sys.argv) > 1 else 'screenshot.png'))

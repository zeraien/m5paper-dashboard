import json
import os
import time
from pathlib import Path

import pytest

# Forecast hour buckets use the process local timezone, as in production (TZ from settings.env).
os.environ['TZ'] = 'Europe/Brussels'
time.tzset()

os.environ.setdefault('YR_IDENTITY', 'tests')
os.environ.setdefault('WEATHER_LAT', '59.91')
os.environ.setdefault('WEATHER_LON', '10.75')
os.environ.setdefault('SCREEN_WIDTH', '540')
os.environ.setdefault('SCREEN_HEIGHT', '960')
os.environ.setdefault('CALENDAR_ICS', 'http://calendar.invalid/basic.ics')

FIXTURES = Path(__file__).parent / 'fixtures'


@pytest.fixture
def forecast_data():
    return json.loads((FIXTURES / 'locationforecast_sample.json').read_text())


@pytest.fixture
def calendar_ics():
    return (FIXTURES / 'calendar.ics').read_bytes()

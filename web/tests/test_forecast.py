from datetime import datetime

import pytest

from einkdisplay.forecast import Forecast, ForecastError, build_forecasts

# 11:30 CEST == 09:30Z; the fixture's first timeseries entry is 09:00Z.
NOW = datetime(2025, 4, 2, 11, 30).astimezone()


def test_build_forecasts_buckets(forecast_data):
    forecasts = build_forecasts(forecast_data, now=NOW, hour_span=6)

    assert [(f.hour_start, f.hour_end) for f in forecasts] == [
        (11, 12), (12, 18), (18, 0), (0, 6)]


def test_current_block_values(forecast_data):
    current = build_forecasts(forecast_data, now=NOW, hour_span=6)[0]

    # single hour 09:00Z: 10.2 °C, 65.1 %, 5.5 m/s
    assert current.temperature == 10
    assert current.wind_speed == 6
    assert current.precipitation == 0
    assert current.symbol_name == 'clearsky_day'
    assert current.symbol_code == '01d'


def test_temperature_is_averaged_over_block(forecast_data):
    block = build_forecasts(forecast_data, now=NOW, hour_span=6)[1]

    # 10:00Z..15:00Z: (11.9 + 13.5 + 15.0 + 15.9 + 16.1 + 16.1) / 6 = 14.75
    assert block.temperature == 15


def test_feels_like(forecast_data):
    current = build_forecasts(forecast_data, now=NOW, hour_span=6)[0]

    # e = 0.651 * 6.105 * exp(17.27 * 10.2 / 247.9) = 8.089
    # AT = 10.2 + 0.33 * 8.089 - 0.70 * 5.5 - 4.00 = 5.02
    assert current.feels_like_degrees == 5


@pytest.mark.parametrize('missing', ['relative_humidity', 'wind_speed'])
def test_feels_like_unknown_when_input_missing(forecast_data, missing):
    for entry in forecast_data['properties']['timeseries']:
        del entry['data']['instant']['details'][missing]

    current = build_forecasts(forecast_data, now=NOW, hour_span=6)[0]

    assert current.feels_like_degrees == '?'


def test_no_matching_timeseries_raises(forecast_data):
    with pytest.raises(ForecastError):
        Forecast(forecast_data, dt=datetime(2030, 1, 1, 12).astimezone(), hour_span=6)

import math
from datetime import datetime, timezone, timedelta
from functools import reduce

import requests

from einkdisplay.weather_symbols import code_to_number_map

API_URL = 'https://api.met.no/weatherapi/locationforecast/2.0/compact'


class ForecastError(Exception):
    pass


def dl_forecast(lat, lng, identity):
    response = requests.get(API_URL, params={'lat': lat, 'lon': lng},
                            headers={'User-Agent': identity}, timeout=30)
    response.raise_for_status()
    return response.json()


def build_forecasts(forecast_data: dict, now: datetime, hour_span: int) -> list:
    """
    One Forecast for the current hour up to the next hour_span boundary,
    followed by three full hour_span blocks.
    """
    hour_list = [now.hour]
    for r in range(0, 3):
        hour_list.append(hour_list[-1] + (hour_span - (hour_list[-1] % hour_span)))

    start_of_day = datetime(now.year, now.month, now.day).astimezone()
    return [Forecast(forecast_data, dt=start_of_day + timedelta(hours=h), hour_span=hour_span)
            for h in hour_list]


class Forecast:
    def __init__(self, forecast_data: dict, dt: datetime, hour_span: int):

        def _fdate(d: datetime):
            return d.strftime("%Y-%m-%dT%H:00:00Z")

        _tz_dt = dt.astimezone(tz=timezone.utc)
        time_list = [_tz_dt+timedelta(hours=h)
                     for h in range(0, hour_span - (_tz_dt.astimezone().hour % hour_span))]

        formatted_time_list = [_fdate(dt) for dt in time_list]
        self._forecasts = [d
                           for d in forecast_data['properties']['timeseries']
                           if d['time'] in formatted_time_list]
        if len(self._forecasts) == 0:
            raise ForecastError(f"No forecast data for {formatted_time_list[0]}")
        self._dt = dt
        self._hour_start = time_list[0].astimezone().hour
        self._hour_end = time_list[-1].astimezone().hour

    def _get_hour_start(self) -> int:
        return self._hour_start
    hour_start = property(_get_hour_start)

    def _get_hour_end(self) -> int:
        return self._hour_end < 23 and self._hour_end+1 or 0
    hour_end = property(_get_hour_end)

    def _get_temperature(self) -> int:
        """
        :return: average temperature from all forecasts in this dataset
        """
        return self._get_avg('instant', 'details', 'air_temperature')
    temperature = property(_get_temperature)

    def _get_mean(self, *keys) -> float:
        d = [reduce(dict.get, keys, f['data']) for f in self._forecasts]
        return sum(d) / len(d)

    def _get_avg(self, *keys) -> int:
        return round(self._get_mean(*keys))

    def _get_feels_like(self):
        """
        Apparent temperature (Australian BOM, without solar radiation), see
        https://code.adonline.id.au/calculating-feels-like-temperatures/
        :return: rounded degrees, or "?" when the inputs are not available
        """
        try:
            temperature = self._get_mean('instant', 'details', 'air_temperature')
            humidity = self._get_mean('instant', 'details', 'relative_humidity')
            wind_speed = self._get_mean('instant', 'details', 'wind_speed')
            vapour_pressure = (humidity / 100 * 6.105
                               * math.exp(17.27 * temperature / (237.7 + temperature)))
            return round(temperature + 0.33 * vapour_pressure - 0.70 * wind_speed - 4.00)
        except (KeyError, TypeError, ValueError, ArithmeticError):
            return "?"
    feels_like_degrees = property(_get_feels_like)

    def _get_precipitation(self) -> float:
        return self._get_avg('next_1_hours', 'details', 'precipitation_amount')
    precipitation = property(_get_precipitation)

    def _get_wind_speed(self) -> int:
        return self._get_avg('instant', 'details', 'wind_speed')
    wind_speed = property(_get_wind_speed)

    def _get_symbol_name(self) -> str:
        return self._forecasts[0]['data']['next_1_hours']['summary']['symbol_code']
    symbol_name = property(_get_symbol_name)

    def _get_symbol_code(self) -> str:
        return code_to_number_map[self.symbol_name]
    symbol_code = property(_get_symbol_code)

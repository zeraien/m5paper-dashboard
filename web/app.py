from datetime import datetime
import os
from flask import Flask, Response

from einkdisplay.calendar import build_days, dl_calendar
from einkdisplay.forecast import build_forecasts, dl_forecast
from einkdisplay.renderer import render_png
from einkdisplay.templating_decorator import templated

app = Flask(__name__)

LAT = os.environ['WEATHER_LAT']
LNG = os.environ['WEATHER_LON']
YR_IDENTITY = os.environ['YR_IDENTITY']
SCREEN_WIDTH = int(os.environ['SCREEN_WIDTH'])
SCREEN_HEIGHT = int(os.environ['SCREEN_HEIGHT'])
CALENDAR_ICS = os.environ['CALENDAR_ICS']
RANGE_SPAN = 6

# Page that is screenshotted for the display, served by this same process.
SCREEN_URL = 'http://127.0.0.1:5000/dashboard'


@app.route('/')
def screen():
    try:
        png = render_png(SCREEN_URL, width=SCREEN_WIDTH, height=SCREEN_HEIGHT)
    except Exception as e:
        app.logger.exception("Rendering %s failed", SCREEN_URL)
        return Response(f"Rendering failed: {e}\n", status=503, mimetype='text/plain')
    return Response(png, mimetype='image/png')


def _weather_context(now):
    forecast_data = dl_forecast(lat=LAT, lng=LNG, identity=YR_IDENTITY)
    return {'forecasts': build_forecasts(forecast_data, now=now, hour_span=RANGE_SPAN)}


def _calendar_context(now):
    ics_data = dl_calendar(CALENDAR_ICS)
    return {'days': build_days(ics_data, now=now)}


@app.route('/dashboard')
@templated("dashboard.html")
def dashboard():
    now = datetime.now().astimezone()
    return _weather_context(now) | _calendar_context(now)


@app.route('/calendar')
@templated("calendar.html")
def calendar():
    return _calendar_context(datetime.now().astimezone())


@app.route('/weather')
@templated("weather.html")
def weather():
    return _weather_context(datetime.now().astimezone())


if __name__ == '__main__':
    app.run()

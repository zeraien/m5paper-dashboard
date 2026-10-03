import pytest

import app as app_module
from einkdisplay.renderer import RenderError


@pytest.fixture
def client():
    return app_module.app.test_client()


def test_screen_returns_png_with_content_length(client, monkeypatch):
    calls = []

    def fake_render(url, width, height):
        calls.append((url, width, height))
        return b'\x89PNG fake'

    monkeypatch.setattr(app_module, 'render_png', fake_render)

    response = client.get('/')

    assert response.status_code == 200
    assert response.mimetype == 'image/png'
    assert response.headers['Content-Length'] == str(len(b'\x89PNG fake'))
    assert calls == [('http://127.0.0.1:5000/dashboard', 540, 960)]


def test_screen_returns_503_when_rendering_fails(client, monkeypatch):
    def failing_render(url, width, height):
        raise RenderError('boom')

    monkeypatch.setattr(app_module, 'render_png', failing_render)

    response = client.get('/')

    assert response.status_code == 503
    assert response.mimetype == 'text/plain'


def test_weather_page_renders(client, monkeypatch, forecast_data):
    monkeypatch.setattr(app_module, 'dl_forecast', lambda lat, lng, identity: forecast_data)
    monkeypatch.setattr(app_module, 'build_forecasts',
                        _with_fixed_now(app_module.build_forecasts))

    response = client.get('/weather')

    assert response.status_code == 200
    assert b'01d.svg' in response.data
    assert b'family=Noto+Sans' in response.data


def test_calendar_page_renders(client, monkeypatch, calendar_ics):
    from datetime import datetime

    build_days = app_module.build_days
    monkeypatch.setattr(app_module, 'dl_calendar', lambda url: calendar_ics)
    monkeypatch.setattr(app_module, 'build_days', lambda ics_data, now: build_days(
        ics_data, now=datetime(2025, 4, 2, 11, 30).astimezone()))

    response = client.get('/calendar')

    assert response.status_code == 200
    assert b'Dentist' in response.data
    assert b'14:00 - 15:00' in response.data
    assert b'Holiday' in response.data
    assert b'All day' not in response.data


def test_dashboard_page_renders(client, monkeypatch, forecast_data, calendar_ics):
    from datetime import datetime

    build_days = app_module.build_days
    monkeypatch.setattr(app_module, 'dl_forecast', lambda lat, lng, identity: forecast_data)
    monkeypatch.setattr(app_module, 'build_forecasts',
                        _with_fixed_now(app_module.build_forecasts))
    monkeypatch.setattr(app_module, 'dl_calendar', lambda url: calendar_ics)
    monkeypatch.setattr(app_module, 'build_days', lambda ics_data, now: build_days(
        ics_data, now=datetime(2025, 4, 2, 11, 30).astimezone()))

    response = client.get('/dashboard')

    assert response.status_code == 200
    assert b'01d.svg' in response.data
    assert b'Dentist' in response.data


def _with_fixed_now(build_forecasts):
    from datetime import datetime

    def wrapper(forecast_data, now, hour_span):
        return build_forecasts(forecast_data, now=datetime(2025, 4, 2, 11, 30).astimezone(),
                               hour_span=hour_span)
    return wrapper

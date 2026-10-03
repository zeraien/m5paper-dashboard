from datetime import date, datetime

import pytest

from einkdisplay.calendar import CalendarError, build_days

# Wednesday 11:30 CEST
NOW = datetime(2025, 4, 2, 11, 30).astimezone()


def _titles(day):
    return [event.title for event in day.events]


def test_today_and_tomorrow(calendar_ics):
    days = build_days(calendar_ics, now=NOW)

    assert [(day.label, day.date) for day in days] == [
        ('Today', date(2025, 4, 2)), ('Tomorrow', date(2025, 4, 3))]


def test_today_events_in_order_without_finished_or_cancelled(calendar_ics):
    today = build_days(calendar_ics, now=NOW)[0]

    # all-day first, then timed by start; Workshop (11:00-12:00) is in progress
    assert _titles(today) == ['Holiday', 'Bin day', 'Workshop', 'Dentist', 'Call with NY']


def test_tomorrow_includes_recurring_and_multi_day_events(calendar_ics):
    tomorrow = build_days(calendar_ics, now=NOW)[1]

    assert _titles(tomorrow) == ['Holiday', 'Weekly sync']


def test_time_range(calendar_ics):
    today, tomorrow = build_days(calendar_ics, now=NOW)
    events = {event.title: event for event in today.events + tomorrow.events}

    assert events['Dentist'].time_range == '14:00 - 15:00'
    assert events['Call with NY'].time_range == '18:00 - 19:00'  # 16:00Z in CEST
    assert events['Weekly sync'].time_range == '10:00 - 10:30'
    assert events['Holiday'].time_range == 'All day'
    assert events['Holiday'].all_day
    assert not events['Dentist'].all_day


def test_missing_title(calendar_ics):
    ics = calendar_ics.replace(b'SUMMARY:Dentist\r\n', b'').replace(b'SUMMARY:Dentist\n', b'')

    today = build_days(ics, now=NOW)[0]

    assert '(no title)' in _titles(today)


def test_invalid_ics_raises():
    with pytest.raises(CalendarError):
        build_days(b'this is not a calendar', now=NOW)

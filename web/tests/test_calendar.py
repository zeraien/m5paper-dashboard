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


def test_short_label(calendar_ics):
    today, tomorrow = build_days(calendar_ics, now=NOW)
    events = {event.title: event for event in today.events + tomorrow.events}

    assert events['Weekly sync'].short_label == '10h Weekly sync'
    assert events['Holiday'].short_label == 'Holiday'


def test_short_label_keeps_minutes_when_not_on_the_hour():
    today = build_days(_generated_ics(2, 0), now=NOW)[0]

    assert [event.short_label for event in today.events] == ['12h 2-0', '12:15 2-1']


def test_missing_title(calendar_ics):
    ics = calendar_ics.replace(b'SUMMARY:Dentist\r\n', b'').replace(b'SUMMARY:Dentist\n', b'')

    today = build_days(ics, now=NOW)[0]

    assert '(no title)' in _titles(today)


def test_invalid_ics_raises():
    with pytest.raises(CalendarError):
        build_days(b'this is not a calendar', now=NOW)


def _generated_ics(today_count, tomorrow_count):
    lines = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//eink-display tests//EN']
    for day, count in (('20250402', today_count), ('20250403', tomorrow_count)):
        for i in range(count):
            lines += ['BEGIN:VEVENT', f'UID:{day}-{i}@test',
                      f'DTSTART;TZID=Europe/Brussels:{day}T{12 + i // 4:02d}{i % 4 * 15:02d}00',
                      f'DTEND;TZID=Europe/Brussels:{day}T{20:02d}0000',
                      f'SUMMARY:{day[-1]}-{i}', 'END:VEVENT']
    lines.append('END:VCALENDAR')
    return '\r\n'.join(lines).encode()


def _visible(day):
    return [event.title for event in day.visible_events]


def _hidden(day):
    return [event.title for event in day.hidden_events]


def test_fixture_with_six_rows(calendar_ics):
    today, tomorrow = build_days(calendar_ics, now=NOW, max_rows=6)

    assert _visible(today) == ['Holiday', 'Bin day', 'Workshop', 'Dentist', 'Call with NY']
    assert _hidden(today) == []
    assert _visible(tomorrow) == []
    assert _hidden(tomorrow) == ['Holiday', 'Weekly sync']


def test_fixture_with_four_rows_drops_tomorrow(calendar_ics):
    days = build_days(calendar_ics, now=NOW, max_rows=4)

    assert [day.label for day in days] == ['Today']
    assert _visible(days[0]) == ['Holiday', 'Bin day', 'Workshop']
    assert _hidden(days[0]) == ['Dentist', 'Call with NY']


def test_no_limit_shows_everything(calendar_ics):
    days = build_days(calendar_ics, now=NOW)

    assert len(days) == 2
    for day in days:
        assert day.visible_events == day.events
        assert day.hidden_events == []


@pytest.mark.parametrize('today_count, tomorrow_count, expected', [
    # (visible, hidden) per shown day
    (8, 4, [(5, 3)]),
    (6, 3, [(6, 0)]),
    (2, 9, [(2, 0), (3, 6)]),
    (0, 3, [(0, 0), (3, 0)]),
    (5, 4, [(5, 0), (0, 4)]),
])
def test_row_allocation(today_count, tomorrow_count, expected):
    days = build_days(_generated_ics(today_count, tomorrow_count), now=NOW, max_rows=6)

    assert [(len(day.visible_events), len(day.hidden_events)) for day in days] == expected

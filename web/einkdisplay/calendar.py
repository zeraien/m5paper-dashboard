from datetime import date, datetime, time, timedelta

import recurring_ical_events
import requests
from icalendar import Calendar


class CalendarError(Exception):
    pass


def dl_calendar(url):
    """
    :return: raw ICS bytes; icalendar decodes them, avoiding requests' charset guessing
    """
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.content


def build_days(ics_data: bytes, now: datetime, max_rows: int = None) -> list:
    """
    CalendarDay for today and tomorrow; events of today that have already ended are left out.
    :param max_rows: limit on event rows across both days, an overflow row included;
        tomorrow is left out unless today has fewer events than this
    """
    try:
        calendar = Calendar.from_ical(ics_data)
    except Exception as e:
        raise CalendarError(f"Unable to parse calendar: {e}") from e

    today_date = now.date()
    today = CalendarDay(calendar, day=today_date, label='Today', now=now)
    tomorrow = CalendarDay(calendar, day=today_date + timedelta(days=1), label='Tomorrow', now=now)
    if max_rows is None:
        return [today, tomorrow]

    today.limit(max_rows)
    if len(today.events) >= max_rows:
        return [today]
    tomorrow.limit(max_rows - len(today.events))
    return [today, tomorrow]


def _local_midnight(d: date) -> datetime:
    return datetime.combine(d, time()).astimezone()


class CalendarDay:
    def __init__(self, calendar: Calendar, day: date, label: str, now: datetime):
        day_start = _local_midnight(day)
        day_end = _local_midnight(day + timedelta(days=1))

        events = [CalendarEvent(component)
                  for component in recurring_ical_events.of(calendar).between(day_start, day_end)
                  if component.get('STATUS') != 'CANCELLED']
        self._events = sorted([e for e in events if e.all_day or e.end > now],
                              key=lambda e: (not e.all_day, e.sort_key))
        self._visible_events = self._events
        self._hidden_events = []
        self._date = day
        self._label = label

    def limit(self, max_rows: int):
        """
        Show at most max_rows rows: when the events do not fit, the last row lists the rest.
        """
        if len(self._events) <= max_rows:
            self._visible_events, self._hidden_events = self._events, []
        else:
            self._visible_events = self._events[:max_rows - 1]
            self._hidden_events = self._events[max_rows - 1:]

    def _get_date(self) -> date:
        return self._date
    date = property(_get_date)

    def _get_label(self) -> str:
        return self._label
    label = property(_get_label)

    def _get_events(self) -> list:
        return self._events
    events = property(_get_events)

    def _get_visible_events(self) -> list:
        return self._visible_events
    visible_events = property(_get_visible_events)

    def _get_hidden_events(self) -> list:
        """
        :return: events that did not fit, shown as one overflow row
        """
        return self._hidden_events
    hidden_events = property(_get_hidden_events)


class CalendarEvent:
    def __init__(self, component):
        self._title = str(component.get('SUMMARY', '')).strip() or '(no title)'
        self._start = component.decoded('DTSTART')
        self._end = component.decoded('DTEND') if 'DTEND' in component else self._start
        self._all_day = not isinstance(self._start, datetime)
        if not self._all_day:
            self._start = self._start.astimezone()
            self._end = self._end.astimezone()

    def _get_title(self) -> str:
        return self._title
    title = property(_get_title)

    def _get_all_day(self) -> bool:
        return self._all_day
    all_day = property(_get_all_day)

    def _get_start(self):
        """
        :return: local datetime, or date for all-day events
        """
        return self._start
    start = property(_get_start)

    def _get_end(self):
        """
        :return: local datetime, or date (exclusive) for all-day events
        """
        return self._end
    end = property(_get_end)

    def _get_sort_key(self) -> datetime:
        return _local_midnight(self._start) if self._all_day else self._start
    sort_key = property(_get_sort_key)

    def _get_time_range(self) -> str:
        if self._all_day:
            return 'All day'
        return f"{self._start:%H:%M} - {self._end:%H:%M}"
    time_range = property(_get_time_range)

    def _get_short_label(self) -> str:
        """
        :return: title preceded by the start time ("10h", or "10:30" when not on the hour),
            e.g. for the overflow row
        """
        if self._all_day:
            return self._title
        start = f"{self._start:%H}h" if self._start.minute == 0 else f"{self._start:%H:%M}"
        return f"{start} {self._title}"
    short_label = property(_get_short_label)

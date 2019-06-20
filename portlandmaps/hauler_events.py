import textwrap
import sys
from datetime import datetime, timedelta
import json

import pytz
import requests
import icalendar

from .utils import millis_since_epoch, sha256_sorted_json, public_api_key


def get_hauler_events_in_range(
    api_key, property_id, frequency, dt_from, dt_to, timeout=10.0
):
    base_url = "https://www.portlandmaps.com/api/detail.cfm"
    headers = {"Referer": "https://www.portlandmaps.com/"}
    params = {
        "detail_type": "hauler",
        "detail_id": property_id,
        "sections": "events",
        "frequency": frequency,
        "api_key": api_key,
        "utc_offset_from": 0,
        "utc_offset_to": 0,
    }

    params["from"] = str(int(millis_since_epoch(dt_from)))
    params["to"] = str(int(millis_since_epoch(dt_to)))

    response = requests.get(base_url, params=params, headers=headers, timeout=timeout)
    response.raise_for_status()
    envelope = response.json()
    if envelope.get("success") and envelope["status"] == "success":
        return envelope["result"]
    else:
        raise RuntimeError(f'Request failed: {envelope["status"]}')


def generate_ics_events_from_pm_events(events):
    for ev in events:
        # example event:
        # {
        #   "title": "Garbage",
        #   "start": 1561554000000,
        #   "end": 1561557600000,
        #   "calendar": "orange",
        #   "id": 1,
        #   "class": "event-garbage"
        # }

        # generate naive datetime from the stamp given in the event; it's always
        # returned in US/Pacific but we don't care because we just extract its
        # date information
        dt = datetime.fromtimestamp(ev["start"] / 1000)
        event_hash = sha256_sorted_json(ev)
        ics_event = icalendar.Event()
        ics_event.add("dtstart", dt.date())
        ics_event.add("uid", f"{event_hash}-hauler-event@portlandmaps.com")
        ics_event.add("summary", ev["title"])
        yield ics_event


def make_ics_calendar_from_pm_events(pm_events, calname="Hauler Pickup"):
    cal = icalendar.Calendar()
    cal.add("prodid", "-//HaulerCal/EN")
    cal.add("version", "2.0")
    for ics_event in generate_ics_events_from_pm_events(pm_events):
        cal.add_component(ics_event)
    return cal


def demo():
    today = pytz.utc.localize(datetime.utcnow())
    pm_events = get_hauler_events_in_range(
        api_key=public_api_key,
        property_id="R206401",
        frequency="eow",
        dt_from=today,
        dt_to=today + timedelta(days=30),
    )
    cal = make_ics_calendar_from_pm_events(pm_events)
    sys.stdout.buffer.write(cal.to_ical())


if __name__ == "__main__":
    demo()

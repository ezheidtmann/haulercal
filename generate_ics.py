#!/usr/bin/env python3
import textwrap
import sys
from datetime import datetime, timedelta
import json
import hashlib

import pytz
import requests
import icalendar

epoch = pytz.utc.localize(datetime(1970, 1, 1, 0, 0, 0))

def sha256_sorted_json(stuff):
    m = hashlib.sha256()
    m.update(json.dumps(stuff, sort_keys=True).encode('utf-8'))
    return m.hexdigest()

def get_hauler_events_in_range(api_key, property_id, frequency, dt_from, dt_to, timeout=10.0):
    base_url = 'https://www.portlandmaps.com/api/detail.cfm'
    headers = {
        'Referer': 'https://www.portlandmaps.com/'
    }
    params = {
        'detail_type': 'hauler',
        'detail_id': property_id,
        'sections': 'events',
        'frequency': frequency,
        'api_key': api_key,
        'utc_offset_from': 0,
        'utc_offset_to': 0,
    }
    # milliseconds since epoch
    params['from'] = str(int((dt_from - epoch).total_seconds() * 1000))
    params['to'] = str(int((dt_to - epoch).total_seconds() * 1000))
    print(json.dumps(params, indent=2), file=sys.stderr)

    response = requests.get(base_url, params=params, headers=headers, timeout=timeout)
    response.raise_for_status()
    envelope = response.json()
    if envelope.get('success') and envelope['status'] == 'success':
        return envelope['result']

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

        # generate naive datetime from the stamp given in the event
        # TODO: verify timezone; empirically these start at 6am in PM display
        dt = datetime.fromtimestamp(ev['start'] / 1000)
        event_hash = sha256_sorted_json(ev)
        ics_event = icalendar.Event()
        ics_event.add('dtstart', dt.date())
        ics_event.add('uid', f'{event_hash}-hauler-event@portlandmaps.com')
        ics_event.add('summary', ev['title'])
        yield ics_event

def write_calendar_from_events(f, events, calname='Hauler Pickup'):
    cal = icalendar.Calendar()
    cal.add('prodid', '-//HaulerCal/EN')
    cal.add('version', '2.0')
    for ics_event in generate_ics_events_from_pm_events(events):
        cal.add_component(ics_event)
    if f is sys.stdout:
        f.buffer.write(cal.to_ical())
    else:
        f.write(cal.to_ical())

def demo():
    today = pytz.utc.localize(datetime.utcnow())
    pm_events = get_hauler_events_in_range(
        api_key='7D700138A0EA40349E799EA216BF82F9', 
        property_id='R206401', 
        frequency='eow', 
        dt_from=today, 
        dt_to=today + timedelta(days=30))
    write_calendar_from_events(sys.stdout, pm_events)

if __name__ == '__main__':
    demo()

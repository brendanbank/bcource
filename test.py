from icalendar import Event, Calendar
import zoneinfo
import datetime as dt
import uuid, time

uuid = uuid.uuid4()
cal = Calendar()
cal.add("prodid", "-//bcourse//bcource//EN")
cal.add("version", "2.0")
cal.add("summary", "Bcourse 2")

event = Event()
event.add('dtstart', dt.datetime(2025, 6, 8, 15, 30, 0, tzinfo=zoneinfo.ZoneInfo('Europe/Amsterdam')))
event.add('dtend',  dt.datetime(2025, 6, 8, 16, 45, 0, tzinfo=zoneinfo.ZoneInfo('Europe/Amsterdam')))
event.add('uid', uuid)
event.add('ORGANIZER;CN="John Doe"','mailto:john.doe@example.com')
event.add('status', "CONFIRMED")
event.add('dtstamp', dt.datetime.now(tz=zoneinfo.ZoneInfo('Europe/Amsterdam')))
event.add('summary', "Morning paper drop-off")
event.add('ATTENDEE;ROLE=REQ-PARTICIPANT;CN="Jane Smith"', 'mailto:jane.smith@example.com')
event.add('location', 'My Rooma')
event.add('DESCRIPTION', 'This is the kick-off meeting')

cal.add_component(event)

with open("/Users/brendan/Downloads/new.ics", "wb") as f:
    f.write(cal.to_ical())

time.sleep(2)

cal = Calendar()
cal.add("prodid", "-//bcourse//bcource//EN")
cal.add("version", "2.0")
cal.add("summary", "Bcourse 2")
cal.add('method', "CANCEL")

event = Event()

time.sleep(1)
event.add('dtstart', dt.datetime(2025, 6, 8, 15, 30, 0, tzinfo=zoneinfo.ZoneInfo('Europe/Amsterdam')))
event.add('dtend',  dt.datetime(2025, 6, 8, 16, 45, 0, tzinfo=zoneinfo.ZoneInfo('Europe/Amsterdam')))
event.add('uid', uuid)
event.add('ORGANIZER;CN="John Doe"','mailto:john.doe@example.com')
event.add('status', "CANCELLED")
event.add('SEQUENCE', 1)
event.add('dtstamp', dt.datetime.now(tz=zoneinfo.ZoneInfo('Europe/Amsterdam')))
event.add('summary', "CANCELLED: Morning paper drop-off")
event.add('ATTENDEE;ROLE=REQ-PARTICIPANT;CN="Jane Smith"', 'mailto:jane.smith@example.com')
event.add('location', 'My Rooma')
event.add('DESCRIPTION', 'This is the kick-off meeting')

cal.add_component(event)
with open("/Users/brendan/Downloads/cancel.ics", "wb") as f:
    f.write(cal.to_ical())

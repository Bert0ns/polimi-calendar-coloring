from googleapiclient.discovery import build


class CalendarClient:
    """Wrapper for Google Calendar API interactions."""

    def __init__(self, credentials):
        self.service = build("calendar", "v3", credentials=credentials)

    def get_calendar_id_by_name(self, name):
        """Finds a calendar ID by its summary (name)."""
        page_token = None
        while True:
            calendar_list = (
                self.service.calendarList().list(pageToken=page_token).execute()
            )
            for calendar_list_entry in calendar_list["items"]:
                if calendar_list_entry["summary"] == name:
                    return calendar_list_entry["id"]
            page_token = calendar_list.get("nextPageToken")
            if not page_token:
                break
        return None

    def create_calendar(self, name):
        """Creates a new calendar and returns its ID."""
        calendar = {"summary": name, "timeZone": "Europe/Rome"}
        created_calendar = self.service.calendars().insert(body=calendar).execute()
        return created_calendar["id"]

    def get_all_events(self, calendar_id):
        """Fetches all events from a specific calendar."""
        events = []
        page_token = None
        while True:
            events_result = (
                self.service.events()
                .list(
                    calendarId=calendar_id,
                    singleEvents=True,
                    orderBy="startTime",
                    pageToken=page_token,
                )
                .execute()
            )
            events.extend(events_result.get("items", []))
            page_token = events_result.get("nextPageToken")
            if not page_token:
                break
        return events

    def insert_event(self, calendar_id, event_body):
        """Inserts a new event into the calendar."""
        return (
            self.service.events()
            .insert(calendarId=calendar_id, body=event_body)
            .execute()
        )

    def update_event(self, calendar_id, event_id, event_body):
        """Updates an entire event."""
        return (
            self.service.events()
            .update(calendarId=calendar_id, eventId=event_id, body=event_body)
            .execute()
        )

    def delete_event(self, calendar_id, event_id):
        """Deletes an event from the calendar."""
        self.service.events().delete(calendarId=calendar_id, eventId=event_id).execute()

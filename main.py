import sys
import os
import argparse
from dotenv import load_dotenv

from auth import Authenticator
from calendar_client import CalendarClient
from strategy import PolimiExamColoringStrategy


class CalendarSyncProcessor:
    """Coordinates syncing from a read-only calendar to a colored writable calendar."""

    def __init__(
        self, client: CalendarClient, strategy, source_name: str, target_name: str, verbose: bool = False
    ):
        self.client = client
        self.strategy = strategy
        self.source_name = source_name
        self.target_name = target_name
        self.verbose = verbose

    def log(self, message):
        """Prints message only if verbose mode is enabled."""
        if self.verbose:
            print(message)

    def process(self):
        print(f"Looking for source calendar '{self.source_name}'...")
        source_id = self.client.get_calendar_id_by_name(self.source_name)

        if not source_id:
            print(f"Error: Source calendar '{self.source_name}' not found.")
            sys.exit(1)

        print(f"Looking for target calendar '{self.target_name}'...")
        target_id = self.client.get_calendar_id_by_name(self.target_name)

        if not target_id:
            print(f"Target calendar not found. Creating '{self.target_name}'...")
            target_id = self.client.create_calendar(self.target_name)

        print("Fetching events from source...")
        source_events = self.client.get_all_events(source_id)
        print(f"Fetched {len(source_events)} source events.")

        print("Fetching events from target...")
        target_events = self.client.get_all_events(target_id)
        target_events_map = {e["id"]: e for e in target_events}
        print(f"Fetched {len(target_events)} target events.")

        source_event_ids = set()

        inserted = 0
        updated = 0
        deleted = 0

        for s_event in source_events:
            event_id = s_event.get("id")
            if not event_id:
                continue

            # Google Calendar requires IDs to be base32hex (a-v, 0-9).
            valid_id = "".join(
                c for c in event_id.lower() if c in "abcdefghijklmnopqrstuv0123456789"
            )

            source_event_ids.add(valid_id)
            
            summary = s_event.get("summary", "")
            self.log(f"Processing event: '{summary}'")

            # Determine new color
            new_color_id = self.strategy.determine_color(s_event)
            if new_color_id:
                self.log(f"  -> Match found! Setting colorId to {new_color_id}")
            else:
                self.log(f"  -> No specific match. Using default calendar color.")

            # Construct body for target event
            t_body = {
                "id": valid_id,
                "summary": summary,
                "description": s_event.get("description", ""),
                "start": s_event.get("start"),
                "end": s_event.get("end"),
            }
            if "location" in s_event:
                t_body["location"] = s_event["location"]
            if new_color_id:
                t_body["colorId"] = new_color_id

            if valid_id in target_events_map:
                # Compare carefully to see if an update is actually needed
                t_event = target_events_map[valid_id]
                needs_update = False
                
                if t_event.get('summary', '') != t_body.get('summary', ''): needs_update = True
                if t_event.get('description', '') != t_body.get('description', ''): needs_update = True
                if t_event.get('location', '') != t_body.get('location', ''): needs_update = True
                if t_event.get('colorId') != t_body.get('colorId'): needs_update = True
                
                s_start = t_body.get('start', {}).get('dateTime', t_body.get('start', {}).get('date'))
                t_start = t_event.get('start', {}).get('dateTime', t_event.get('start', {}).get('date'))
                if s_start != t_start: needs_update = True
                
                s_end = t_body.get('end', {}).get('dateTime', t_body.get('end', {}).get('date'))
                t_end = t_event.get('end', {}).get('dateTime', t_event.get('end', {}).get('date'))
                if s_end != t_end: needs_update = True
                
                if needs_update:
                    try:
                        self.client.update_event(target_id, valid_id, t_body)
                        updated += 1
                        self.log(f"  -> Event has changes. Updated in target calendar.")
                        import time; time.sleep(0.5) # Avoid rate limits
                    except Exception as e:
                        print(f"Failed to update '{summary}' - {e}")
                else:
                    self.log(f"  -> Event is identical. Skipped update.")
            else:
                try:
                    self.client.insert_event(target_id, t_body)
                    inserted += 1
                    self.log(f"  -> Event is new. Inserted into target calendar.")
                    import time; time.sleep(0.5) # Avoid rate limits
                except Exception as e:
                    print(f"Failed to insert '{summary}' - {e}")

        # Delete events that no longer exist in source
        for t_event_id in target_events_map:
            if t_event_id not in source_event_ids:
                try:
                    self.client.delete_event(target_id, t_event_id)
                    deleted += 1
                    self.log(f"Deleted old event ID '{t_event_id}' that no longer exists in source.")
                    import time; time.sleep(0.5) # Avoid rate limits
                except Exception as e:
                    print(f"Failed to delete '{t_event_id}' - {e}")

        print(
            f"Finished sync. Inserted: {inserted}, Updated: {updated}, Deleted: {deleted}"
        )
        print(
            f"IMPORTANT: Open your Google Calendar and HIDE the original '{self.source_name}' calendar."
        )
        print(f"You will now use '{self.target_name}' to see your colored events!")


def main():
    parser = argparse.ArgumentParser(description="Sync and color Google Calendar events.")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging to see exactly what is happening to each event.")
    parser.add_argument("-i", "--interactive", action="store_true", help="Ask interactively if you are subscribed to each exam.")
    args = parser.parse_args()

    load_dotenv()
    
    source_name = os.getenv("SOURCE_CALENDAR_NAME", "Polimi 11163057")
    target_name = os.getenv("TARGET_CALENDAR_NAME", "Polimi 11163057 Colored")
    credentials_path = os.getenv("CREDENTIALS_PATH", "credentials.json")

    authenticator = Authenticator(credentials_path=credentials_path)
    try:
        creds = authenticator.get_credentials()
    except FileNotFoundError:
        print(f"Error: '{credentials_path}' not found.")
        sys.exit(1)

    client = CalendarClient(credentials=creds)
    strategy = PolimiExamColoringStrategy(interactive=args.interactive)

    processor = CalendarSyncProcessor(
        client=client,
        strategy=strategy,
        source_name=source_name,
        target_name=target_name,
        verbose=args.verbose
    )
    processor.process()


if __name__ == "__main__":
    main()

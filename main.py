import sys
from auth import Authenticator
from calendar_client import CalendarClient
from strategy import PolimiExamColoringStrategy

class CalendarSyncProcessor:
    """Coordinates syncing from a read-only calendar to a colored writable calendar."""
    
    def __init__(self, client: CalendarClient, strategy, source_name: str, target_name: str):
        self.client = client
        self.strategy = strategy
        self.source_name = source_name
        self.target_name = target_name

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
        target_events_map = {e['id']: e for e in target_events}
        print(f"Fetched {len(target_events)} target events.")
        
        source_event_ids = set()
        
        inserted = 0
        updated = 0
        deleted = 0
        
        for s_event in source_events:
            event_id = s_event.get('id')
            if not event_id:
                continue
                
            # Google Calendar requires IDs to be base32hex (a-v, 0-9).
            # The original IDs from the imported calendar might start with '_' or contain invalid chars.
            valid_id = ''.join(c for c in event_id.lower() if c in 'abcdefghijklmnopqrstuv0123456789')
            
            source_event_ids.add(valid_id)
            
            # Determine new color
            new_color_id = self.strategy.determine_color(s_event)
            
            # Construct body for target event
            # We copy only standard fields to avoid API errors with read-only properties
            t_body = {
                'id': valid_id,
                'summary': s_event.get('summary', ''),
                'description': s_event.get('description', ''),
                'start': s_event.get('start'),
                'end': s_event.get('end')
            }
            if 'location' in s_event:
                t_body['location'] = s_event['location']
            if new_color_id:
                t_body['colorId'] = new_color_id

            if valid_id in target_events_map:
                # Compare briefly if an update is needed
                try:
                    self.client.update_event(target_id, valid_id, t_body)
                    updated += 1
                except Exception as e:
                    print(f"Failed to update {s_event.get('summary')} - {e}")
            else:
                try:
                    self.client.insert_event(target_id, t_body)
                    inserted += 1
                except Exception as e:
                    print(f"Failed to insert {s_event.get('summary')} - {e}")

        # Delete events that no longer exist in source
        for t_event_id in target_events_map:
            if t_event_id not in source_event_ids:
                try:
                    self.client.delete_event(target_id, t_event_id)
                    deleted += 1
                except Exception as e:
                    print(f"Failed to delete {t_event_id} - {e}")

        print(f"Finished sync. Inserted: {inserted}, Updated: {updated}, Deleted: {deleted}")
        print(f"IMPORTANT: Open your Google Calendar and HIDE the original '{self.source_name}' calendar.")
        print(f"You will now use '{self.target_name}' to see your colored events!")


def main():
    authenticator = Authenticator(credentials_path='credentials.json')
    try:
        creds = authenticator.get_credentials()
    except FileNotFoundError:
        print("Error: 'credentials.json' not found.")
        sys.exit(1)
    
    client = CalendarClient(credentials=creds)
    strategy = PolimiExamColoringStrategy()
    
    processor = CalendarSyncProcessor(
        client=client, 
        strategy=strategy, 
        source_name="Polimi 11163057",
        target_name="Polimi 11163057 Colored"
    )
    processor.process()

if __name__ == '__main__':
    main()

import sys
import os
import argparse
import time
from dotenv import load_dotenv

from auth import Authenticator
from calendar_client import CalendarClient
from strategy import (
    CompositeColoringStrategy,
    ExamColoringStrategy,
    LectureColoringStrategy,
)


class Colors:
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"


class CalendarSyncProcessor:
    """Coordinates syncing from a read-only calendar to a colored writable calendar."""

    def __init__(
        self,
        client: CalendarClient,
        strategy,
        source_name: str,
        target_name: str,
        verbose: bool = False,
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
        print(
            f"\n{Colors.OKCYAN}{Colors.BOLD}🔍 Syncing '{self.source_name}' ➔ '{self.target_name}'{Colors.ENDC}"
        )

        source_id = self.client.get_calendar_id_by_name(self.source_name)
        if not source_id:
            print(
                f"{Colors.FAIL}✖ Source calendar '{self.source_name}' not found.{Colors.ENDC}"
            )
            sys.exit(1)

        target_id = self.client.get_calendar_id_by_name(self.target_name)
        if not target_id:
            print(
                f"{Colors.WARNING}⚠ Target calendar not found. Creating '{self.target_name}'...{Colors.ENDC}"
            )
            target_id = self.client.create_calendar(self.target_name)

        source_events = self.client.get_all_events(source_id)
        target_events = self.client.get_all_events(target_id)
        target_events_map = {e["id"]: e for e in target_events}

        print(
            f"{Colors.OKBLUE}📥 Fetched {len(source_events)} source & {len(target_events)} target events.{Colors.ENDC}"
        )

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
            self.log(f"\n{Colors.BOLD}Event: {summary}{Colors.ENDC}")

            # Determine new color
            new_color_id = self.strategy.determine_color(s_event)

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
                self.log(
                    f" ↳ {Colors.OKCYAN}Strategy matched (colorId: {new_color_id}){Colors.ENDC}"
                )
                t_body["colorId"] = new_color_id
            elif (
                valid_id in target_events_map
                and "colorId" in target_events_map[valid_id]
            ):
                # CRITICAL: If the strategy doesn't enforce a color (e.g. user skipped lectures),
                # preserve the existing color so we don't accidentally wipe it!
                preserved_color = target_events_map[valid_id]["colorId"]
                self.log(
                    f" ↳ {Colors.OKBLUE}Strategy skipped, preserving existing color (colorId: {preserved_color}){Colors.ENDC}"
                )
                t_body["colorId"] = preserved_color
            else:
                self.log(f" ↳ {Colors.OKBLUE}Using default calendar color{Colors.ENDC}")

            if valid_id in target_events_map:
                # Compare carefully to see if an update is actually needed
                t_event = target_events_map[valid_id]
                needs_update = False

                if t_event.get("summary", "") != t_body.get("summary", ""):
                    needs_update = True
                if t_event.get("description", "") != t_body.get("description", ""):
                    needs_update = True
                if t_event.get("location", "") != t_body.get("location", ""):
                    needs_update = True
                if t_event.get("colorId") != t_body.get("colorId"):
                    needs_update = True

                s_start = t_body.get("start", {}).get(
                    "dateTime", t_body.get("start", {}).get("date")
                )
                t_start = t_event.get("start", {}).get(
                    "dateTime", t_event.get("start", {}).get("date")
                )
                if s_start != t_start:
                    needs_update = True

                s_end = t_body.get("end", {}).get(
                    "dateTime", t_body.get("end", {}).get("date")
                )
                t_end = t_event.get("end", {}).get(
                    "dateTime", t_event.get("end", {}).get("date")
                )
                if s_end != t_end:
                    needs_update = True

                if needs_update:
                    try:
                        self.client.update_event(target_id, valid_id, t_body)
                        updated += 1
                        self.log(
                            f" ↳ {Colors.OKGREEN}Updated in target calendar{Colors.ENDC}"
                        )
                        time.sleep(0.2)  # Avoid rate limits
                    except Exception as e:
                        print(
                            f"{Colors.FAIL}✖ Failed to update '{summary}' - {e}{Colors.ENDC}"
                        )
                else:
                    self.log(f" ↳ {Colors.WARNING}Identical (Skipped){Colors.ENDC}")
            else:
                try:
                    self.client.insert_event(target_id, t_body)
                    inserted += 1
                    self.log(
                        f" ↳ {Colors.OKGREEN}Inserted into target calendar{Colors.ENDC}"
                    )
                    time.sleep(0.2)  # Avoid rate limits
                except Exception as e:
                    print(
                        f"{Colors.FAIL}✖ Failed to insert '{summary}' - {e}{Colors.ENDC}"
                    )

        # Delete events that no longer exist in source
        for t_event_id in target_events_map:
            if t_event_id not in source_event_ids:
                try:
                    self.client.delete_event(target_id, t_event_id)
                    deleted += 1
                    self.log(
                        f" ↳ {Colors.FAIL}Deleted old event ID '{t_event_id}'{Colors.ENDC}"
                    )
                    time.sleep(0.2)  # Avoid rate limits
                except Exception as e:
                    print(
                        f"{Colors.FAIL}✖ Failed to delete '{t_event_id}' - {e}{Colors.ENDC}"
                    )

        print(f"\n{Colors.OKGREEN}{Colors.BOLD}✔ Finished Sync!{Colors.ENDC}")
        print(f"  Inserted: {Colors.OKGREEN}{inserted}{Colors.ENDC}")
        print(f"  Updated:  {Colors.WARNING}{updated}{Colors.ENDC}")
        print(f"  Deleted:  {Colors.FAIL}{deleted}{Colors.ENDC}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Sync and color Google Calendar events."
    )
    parser.add_argument(
        "target",
        choices=["exams", "lectures"],
        help="Mandatory: Specify what to process (exams or lectures).",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging to see exactly what is happening to each event.",
    )
    parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="Ask interactively if you are subscribed to each exam.",
    )
    args = parser.parse_args()

    load_dotenv()

    source_name = os.getenv("SOURCE_CALENDAR_NAME", "Polimi 11163057")
    target_name = os.getenv("TARGET_CALENDAR_NAME", "Polimi 11163057 Colored")
    credentials_path = os.getenv("CREDENTIALS_PATH", "credentials.json")

    strategies_to_use = []
    if args.target == "exams":
        strategies_to_use.append(ExamColoringStrategy(interactive=args.interactive))
    elif args.target == "lectures":
        strategies_to_use.append(LectureColoringStrategy(interactive=args.interactive))

    authenticator = Authenticator(credentials_path=credentials_path)
    try:
        creds = authenticator.get_credentials()
    except FileNotFoundError:
        print(f"{Colors.FAIL}Error: '{credentials_path}' not found.{Colors.ENDC}")
        sys.exit(1)

    client = CalendarClient(credentials=creds)
    strategy = CompositeColoringStrategy(strategies_to_use)

    processor = CalendarSyncProcessor(
        client=client,
        strategy=strategy,
        source_name=source_name,
        target_name=target_name,
        verbose=args.verbose,
    )
    processor.process()


if __name__ == "__main__":
    main()

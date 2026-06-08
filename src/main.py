import sys
import os
import argparse
from dotenv import load_dotenv

from auth import Authenticator
from calendar_client import CalendarClient
from colors import Colors
from sync_processor import CalendarSyncProcessor
from strategies import (
    CompositeColoringStrategy,
    ExamColoringStrategy,
    LectureColoringStrategy,
)


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
        help="Ask interactively if you are subscribed to each exam or pick lecture colors.",
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

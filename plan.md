# Plan for Google Calendar Coloring Script

## 1. Overview

The goal is to create a script that connects to your Google Calendar, finds a specific calendar ("Polimi 11163057"), and updates the colors of specific events based on their titles and descriptions.

**Coloring Rules:**

- Title starts with `"Esame: "` AND Description starts with `"Non iscritto"` -> **Grey**
- Title starts with `"Esame: "` AND Description starts with `"Iscritto"` -> **Red**

## 2. Technology Stack

- **Language**: Python 3. Python is excellent for this task due to its conciseness and the robust, official Google API client libraries.
- **Libraries**:
  - `google-api-python-client`: For interacting with the Google Calendar API.
  - `google-auth-httplib2`, `google-auth-oauthlib`: For handling OAuth 2.0 user authentication.
  - `icalendar` and `requests`: As a fallback to parse the ical link directly if the calendar is read-only.

## 3. Potential Challenge: Subscribed Calendars

You mentioned importing the calendar via an iCal link (`https://ical-polimiapp.polimi.it/11163057/w54N2gYpyJqRCpWU6UFGNgNqAfnMsSAJ`).

- When a calendar is added via URL in Google Calendar, it is considered a "subscribed" calendar.
- The Google Calendar API generally requires "writer" access to a calendar to modify events (including their colors).
- If the API rejects color modifications because the calendar is read-only, our alternative approach will be implemented instead:
  1. Read the events directly from the `.ics` URL using the `requests` and `icalendar` libraries.
  2. Sync them to a _new_, writable secondary Google Calendar that you own (e.g. "Polimi Exams Colored").
  3. Apply the colors before or during the sync.

_For now, the plan will assume we will write a script that can either color an existing writable calendar, or sync from the iCal link to a writable calendar._

## 4. Architecture (SOLID Principles)

To keep the code tidy, well-organized, and compliant with SOLID principles, we will structure it into distinct components:

1. **`Authenticator` (SRP)**: Responsible solely for handling Google OAuth 2.0 authentication and token management.
2. **`CalendarClient` (SRP, DIP)**: A wrapper around the Google Calendar API. Handles fetching calendars, fetching events, and patching/inserting events.
3. **`EventColoringStrategy` (OCP, SRP)**: An interface/abstract base class for coloring rules. We will implement rules like `PolimiExamColoringStrategy`. If you want to add more rules later, you just create a new strategy without modifying existing code.
4. **`EventSyncer`**: Coordinates reading events (either from API or iCal), applying the `EventColoringStrategy`, and updating the events back via the `CalendarClient`.

## 5. Setup Requirements (Prerequisites)

Before running the script, you will need to:

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project.
3. Enable the **Google Calendar API**.
4. Configure the OAuth Consent Screen.
5. Create Credentials (OAuth client ID for a Desktop application) and download the `credentials.json` file.
6. Place `credentials.json` in the same directory as the script.

## 6. Implementation Steps

1. **Initialize Project**: Set up a virtual environment and create `requirements.txt`.
2. **Write the Code**: Implement the classes described in the architecture.
3. **Map Colors**: Google Calendar API uses specific string IDs for colors.
   - Red = `'11'` (Tomato)
   - Grey = `'8'` (Graphite)
4. **Deliver Code**: Provide the full `main.py` script.

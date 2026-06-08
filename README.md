# Polimi Calendar Coloring Sync

This script connects to your Google Calendar and synchronizes events from a read-only Polimi iCal subscription into a new, fully customizable Google Calendar. During the synchronization, it automatically color-codes your exams based on your enrollment status!

### Features
- Connects to your Google account using OAuth 2.0.
- Reads events from a specified source calendar (e.g., `"Polimi 11163057"`).
- Synchronizes these events into a new target calendar (e.g., `"Polimi 11163057 Colored"`).
- Automatically applies the following color rules to your exams:
  - If the Title starts with `"Esame: "` and Description starts with `"Iscritto"`, the event is colored **Red**.
  - If the Title starts with `"Esame: "` and Description starts with `"Non iscritto"`, the event is colored **Grey**.

## Prerequisites

1. **Python 3**: Make sure Python 3 is installed on your system.
2. **Google Cloud Account**: You need a Google Cloud account to generate API credentials.

## Setup Instructions

### 1. Configure Google Cloud Credentials
Because this script accesses your personal Google Calendar, you must create your own API credentials:

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a **New Project**.
3. In the sidebar, navigate to **APIs & Services** > **Library** and enable the **Google Calendar API**.
4. Go to **APIs & Services** > **OAuth consent screen**:
   - Choose **External** user type.
   - Fill in the required app details (name, email).
   - **Important**: Scroll down to the **Test users** section, click **+ ADD USERS**, and add your own Google email address. Without this, you will get a `403 Access Denied` error during login.
5. Go to **APIs & Services** > **Credentials**:
   - Click **+ CREATE CREDENTIALS** > **OAuth client ID**.
   - Select **Desktop app** as the application type.
   - Click Create, then download the JSON file.
6. Rename the downloaded file to `credentials.json` and place it in the same directory as this README.

### 2. Install Dependencies
Open a terminal in the project directory and run:
```bash
pip install -r requirements.txt
```

## Usage

Run the main script:
```bash
python3 main.py
```

**First Time Run:**
1. A browser window will open asking you to log in to your Google Account.
2. You will likely see a warning saying "Google hasn't verified this app". Click **Advanced** -> **Go to [App Name] (unsafe)**. This is perfectly normal since you just created the app yourself.
3. Grant the requested permissions to manage your calendars.

The script will now look for your original calendar, create the "Colored" version, and synchronize all the events with the correct colors applied!

## Important Note
Because the script creates a *copy* of your exams to color them, **you should hide the original calendar** in your Google Calendar web interface or mobile app. Otherwise, you will see duplicates of every event! You can do this by unchecking the box next to the original "Polimi 11163057" calendar in the sidebar.

## Architecture
The code follows SOLID principles:
- `auth.py`: Handles Google OAuth 2.0.
- `calendar_client.py`: Wrapper for Google API interactions.
- `strategy.py`: Contains the logic for the colors (Open/Closed principle).
- `main.py`: Coordinates the sync process.

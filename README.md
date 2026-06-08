# Polimi Calendar Coloring Sync

This script connects to your Google Calendar and synchronizes events from a read-only Polimi iCal subscription into a new, fully customizable Google Calendar. During the synchronization, it automatically color-codes your exams based on your enrollment status!

### Features

- **Intelligent Synchronization**: Safely copies events from a source calendar to a target calendar, updating only what has changed to minimize API calls and avoid rate limits.
- **Auto-Coloring Exams**: Automatically colors exams **Red** if you are subscribed ("Iscritto") and **Grey** if you are not ("Non iscritto").
- **Auto-Coloring Lectures**: Automatically assigns unique, consistent colors to different courses ("Lezione: Didattica - [Course Name]"). 
- **Interactive Mode**: Optionally run the script with `-i` to manually choose exactly which exams you are subscribed to, and manually assign specific colors to your courses!
- **Persistent Memory**: Saves your course color choices to `course_colors.json` so your calendar stays perfectly color-coordinated across future syncs.
- **Environment Configuration**: Easily configure calendar names and credentials paths using a `.env` file.
- **Beautiful Terminal Output**: Features a concise, color-coded ANSI terminal interface so you know exactly what is happening.

---

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

### 2. Configure Environment Variables

Copy the provided `.env.example` file to create your own `.env` file:

```bash
cp .env.example .env
```

Inside `.env`, you can customize the names of your source and target calendars if they differ from the defaults.

### 3. Install Dependencies

Open a terminal in the project directory and run:

```bash
pip install -r requirements.txt
```

---

## Usage

Run the main script:

```bash
python3 main.py
```

**First Time Run:**

1. A browser window will open asking you to log in to your Google Account.
2. You will likely see a warning saying "Google hasn't verified this app". Click **Advanced** -> **Go to [App Name] (unsafe)**. This is perfectly normal since you just created the app yourself.
3. Grant the requested permissions to manage your calendars.

### Command Line Flags

You can customize the script's behavior using the following flags:

- **`-i` or `--interactive`**: Enables interactive mode. The script will pause on every exam it finds and ask if you are subscribed.
  - It will parse the event description to offer a `[Suggested: y/n]` answer—just press `Enter` to accept the suggestion.
  - _Smart tracking_: Once you answer `y` to an exam on a specific date, it will automatically decline any other dates for that exact same exam!
- **`-v` or `--verbose`**: Enables detailed logging. By default, the script only prints a short summary of how many events were inserted, updated, or deleted. With verbose mode, you'll see a color-coded log of the decision-making process for every single event.

Example combining both flags:

```bash
python3 main.py -i -v
```

---

## Important Note

Because the script creates a _copy_ of your exams to color them, **you should hide the original calendar** in your Google Calendar web interface or mobile app. Otherwise, you will see duplicates of every event! You can do this by unchecking the box next to the original "Polimi <student_id>" calendar in the sidebar.

## Architecture

The code follows SOLID principles:

- `auth.py`: Handles Google OAuth 2.0.
- `calendar_client.py`: Wrapper for Google API interactions.
- `strategy.py`: Contains the logic for the colors and interactive prompting (Open/Closed principle).
- `main.py`: Coordinates the sync process, configures the environment, and manages the command line interface.

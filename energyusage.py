import os
import csv
import asyncio
from datetime import date, timedelta

import requests
from dotenv import load_dotenv
from py_aosmith import AOSmithAPIClient

# Loads a local .env if present. Harmless on GitHub Actions (no file there).
load_dotenv()

# --- CREDENTIALS (required) ---
EMAIL = os.environ["AOSMITH_EMAIL"]
PASSWORD = os.environ["AOSMITH_PASSWORD"]
MAILGUN_API_KEY = os.environ["MAILGUN_API_KEY"]
MAILGUN_DOMAIN = os.environ["MAILGUN_DOMAIN"]
NOTIFY_EMAIL = os.environ["NOTIFY_EMAIL"]

# --- SETTINGS (optional, with defaults) ---
THRESHOLD_KWH = float(os.environ.get("THRESHOLD_KWH", "3.0"))
CSV_FILENAME = os.environ.get("CSV_FILENAME", "aosmith_daily_usage.csv")


def parse_entry_date(raw):
    # API dates look like '2023-12-09T04:00:00.000Z'. Keep just the date part.
    return raw[:10]


def already_logged(target_date):
    if not os.path.exists(CSV_FILENAME):
        return False
    with open(CSV_FILENAME, newline="") as f:
        return any(row and row[0] == target_date for row in csv.reader(f))


def append_row(target_date, kwh):
    new_file = not os.path.exists(CSV_FILENAME)
    with open(CSV_FILENAME, "a", newline="") as f:
        writer = csv.writer(f)
        if new_file:
            writer.writerow(["date", "kwh"])
        writer.writerow([target_date, kwh])


def send_alert(target_date, kwh):
    requests.post(
        f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
        auth=("api", MAILGUN_API_KEY),
        data={
            "from": f"Energy Monitor <mailgun@{MAILGUN_DOMAIN}>",
            "to": NOTIFY_EMAIL,
            "subject": f"High water heater usage: {kwh} kWh on {target_date}",
            "text": (
                f"Your water heater used {kwh} kWh on {target_date}, "
                f"above your {THRESHOLD_KWH} kWh threshold."
            ),
        },
    ).raise_for_status()


async def main():
    yesterday = (date.today() - timedelta(days=1)).isoformat()

    if already_logged(yesterday):
        print(f"{yesterday} already logged. Nothing to do.")
        return

    client = AOSmithAPIClient(EMAIL, PASSWORD)
    devices = await client.get_devices()
    if not devices:
        print("No devices found.")
        await client.close()
        return

    device = devices[0]
    energy = await client.get_energy_use_data(device.junction_id)
    await client.close()

    history = getattr(energy, "history", None)
    if not history:
        print("No usage history returned.")
        return

    # Find yesterday's entry
    match = next(
        (e for e in history if parse_entry_date(e.date) == yesterday),
        None,
    )
    if match is None:
        print(f"No entry for {yesterday} yet. Will retry next run.")
        return

    kwh = match.energy_use_kwh
    append_row(yesterday, kwh)
    print(f"Logged {yesterday}: {kwh} kWh")

    # Write the commit message for the workflow to pick up
    with open("commit_msg.txt", "w") as f:
        f.write(f"Usage {yesterday}: {kwh} kWh")

    if kwh > THRESHOLD_KWH:
        send_alert(yesterday, kwh)
        print(f"Alert sent ({kwh} kWh over {THRESHOLD_KWH}).")


asyncio.run(main())

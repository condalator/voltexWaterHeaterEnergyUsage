# A.O. Smith Daily Energy Monitor

Polls your A.O. Smith (iCOMM) water heater once a day, logs the previous
day's energy use to a CSV, and emails you when usage exceeds a threshold.
Runs free on GitHub Actions.

## What it does

Each run:
1. Fetches yesterday's energy reading.
2. Appends `date,kwh` to a CSV (skips dates already logged, so reruns are safe).
3. Commits the CSV with a message like `Usage 2026-06-25: 4.2 kWh`.
4. Emails you via Mailgun **only if** usage tops the threshold.

## Setup: GitHub Actions (recommended)

1. Create a repo and add these files:
   - `energyusage.py` and `requirements.txt` at the root
   - `daily.yml` at `.github/workflows/daily.yml`
2. Add repo secrets (Settings -> Secrets and variables -> Actions):
   - `AOSMITH_EMAIL`
   - `AOSMITH_PASSWORD`
   - `MAILGUN_API_KEY`
   - `MAILGUN_DOMAIN`
   - `NOTIFY_EMAIL`
3. Optional settings: add `THRESHOLD_KWH` or `CSV_FILENAME` to the
   `env:` block in `daily.yml`, or leave them to use the defaults.
4. Trigger it manually once from the Actions tab to test, then let the
   daily schedule take over.

### Changing the schedule

Edit the cron line in `daily.yml`. It is in **UTC**:

```yaml
- cron: "0 10 * * *"   # 10:00 UTC daily
```

Make sure the time is late enough that yesterday's reading has appeared
in iCOMM. If a reading is missing, the script just skips and retries
next run.

## Setup: running locally

1. `python3 -m venv venv && source venv/bin/activate`
2. `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and fill in your values.
4. `python energyusage.py`

Add `.env` to your `.gitignore` so credentials never get committed.

## A note on privacy

If your repo is **public**, the committed CSV and the commit messages
(e.g. `Usage 2026-06-25: 4.2 kWh`) are visible to anyone. Use a
**private repo** if you'd rather keep your usage data to yourself.
Either way, credentials stay safe as long as they live in secrets and
your `.env` is gitignored, never in the code.

## Settings

| Variable        | Default                     | Description                          |
|-----------------|-----------------------------|--------------------------------------|
| `THRESHOLD_KWH` | `3.0`                       | Email alert fires above this value.  |
| `CSV_FILENAME`  | `aosmith_daily_usage.csv`   | Where readings are stored.           |

# iPhone Health Sync

This project can receive daily Apple Health summaries from iPhone Shortcuts.

The recommended cloud flow is:

```text
Apple Watch records activity
-> iPhone Health app stores it
-> iPhone Shortcut builds a small JSON dictionary
-> POST to Google Apps Script Web App
-> Apps Script writes a Google Sheet row
-> Streamlit Apple Health tab reads the sheet
```

This works when your laptop is not with you because the receiver lives on Google, not on your Mac.

## How It Works

`apple_health_receiver.gs` is a tiny Google Apps Script API.

It exposes:

- `GET /exec`: health check
- `POST /exec`: accepts JSON from Shortcuts

Each POST is normalised into the `Health Daily` sheet with these columns:

- `date`
- `steps`
- `active_energy_kcal`
- `exercise_minutes`
- `stand_hours`
- `distance_km`
- `resting_heart_rate`
- `avg_heart_rate`
- `sleep_hours`
- `deep_sleep_hours`
- `rem_sleep_hours`
- `source`
- `received_at`

Rows are upserted by date. If the Shortcut runs twice for the same date, the newest data replaces that date's row.

## Set Up The Google Apps Script API

1. Go to https://script.google.com.
2. Create a new project.
3. Paste the contents of `apple_health_receiver.gs`.
4. Save the project as `Training Lab Apple Health Receiver`.
5. In the left sidebar, open `Project Settings`.
6. Make sure the script is attached to a spreadsheet, or create a new Google Sheet and use `Extensions > Apps Script` from that sheet.
7. Click `Deploy > New deployment`.
8. Select type: `Web app`.
9. Description: `Training Lab Health Receiver`.
10. Execute as: `Me`.
11. Who has access: `Anyone`.
12. Click `Deploy`.
13. Authorise the permissions.
14. Copy the Web App URL. It ends with `/exec`.

That `/exec` URL is the endpoint your iPhone Shortcut will POST to.

## Connect The Sheet To Streamlit

Open the Google Sheet created/used by the script.

Share it as:

```text
Anyone with the link can view
```

Then in Streamlit:

1. Paste the Sheet URL into the sidebar field `Apple Health Sheet URL`.
2. Or add it to `.streamlit/secrets.toml`:

```toml
health_sheet_url = "https://docs.google.com/spreadsheets/d/..."
```

For Streamlit Community Cloud, add the same secret named `health_sheet_url`.

## Shortcut Payload

Start with only a few fields:

```json
{
  "date": "2026-06-07",
  "steps": 8500,
  "active_energy_kcal": 520,
  "exercise_minutes": 48,
  "avg_heart_rate": 112,
  "sleep_hours": 7.4,
  "source": "iphone_shortcuts"
}
```

Supported fields:

- `date`
- `steps`
- `active_energy_kcal`
- `exercise_minutes`
- `stand_hours`
- `distance_km`
- `resting_heart_rate`
- `avg_heart_rate`
- `sleep_hours`
- `deep_sleep_hours`
- `rem_sleep_hours`
- `source`

## Shortcut Setup

In iPhone Shortcuts:

1. Add `Current Date`.
2. Format Date as `yyyy-MM-dd`.
3. Add `Find Health Samples` for each metric you care about, such as Steps and Active Energy.
4. Use statistics where needed, such as sum for Steps and Active Energy.
5. Add `Dictionary`.
6. Add fields such as:
   - `date`: formatted date
   - `steps`: steps total
   - `active_energy_kcal`: active energy total
   - `exercise_minutes`: exercise minutes total
   - `avg_heart_rate`: average heart rate
   - `sleep_hours`: sleep duration
7. Add `Get Contents of URL`.
8. URL: your Apps Script Web App URL ending in `/exec`.
9. Method: `POST`.
10. Request Body: `JSON`.
11. JSON body: the Dictionary from step 5.

Run it once manually first. Then check the Google Sheet. If the row appears there, Streamlit can read it.

## Automation

Once manual testing works:

1. In Shortcuts, go to `Automation`.
2. Create a `Time of Day` automation, for example 23:30.
3. Add `Run Shortcut`.
4. Choose the health sync shortcut.
5. Turn off `Ask Before Running` or choose `Run Immediately`.

## Optional Token

`apple_health_receiver.gs` has:

```javascript
const OPTIONAL_TOKEN = '';
```

If you set this to a secret value, include the same `token` field in your Shortcut dictionary:

```json
{
  "token": "your-secret",
  "date": "2026-06-07",
  "steps": 8500
}
```

For a personal low-risk project, leaving this blank is simpler. If you share the Web App URL widely, add a token.

## Local FastAPI Option

`health_receiver.py` is still available as a learning path for real API development.

It works like this:

```text
iPhone Shortcut -> local Mac FastAPI server -> local CSV -> Streamlit
```

But it only works when your iPhone can reach your Mac, so it is less practical than Google Apps Script for automatic sync.

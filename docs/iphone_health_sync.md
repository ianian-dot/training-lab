# iPhone Health Sync

This project can receive daily Apple Health summaries from iPhone Shortcuts.

The flow is:

```text
Apple Watch records activity
-> iPhone Health app stores it
-> iPhone Shortcut builds a small JSON dictionary
-> POST to Training Lab receiver
-> receiver writes data/apple_health_daily.csv
-> Streamlit Apple Health tab reads the CSV
```

## Important Limitation

A local server on your Mac only works when your iPhone can reach your Mac.

That means:

- It works well for testing on the same Wi-Fi.
- It can work as a nightly home sync if your Mac is awake and your iPhone is on the same Wi-Fi.
- It will not receive data while you are at the gym if your laptop is at home and unreachable.

For real anywhere sync, deploy the receiver to a small cloud service such as Render, Fly.io, Railway, or a private VPS, then point the Shortcut to that HTTPS URL.

## Local Test

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the receiver:

```bash
python3 health_receiver.py
```

Find your Mac's local IP address:

```bash
ipconfig getifaddr en0
```

Your iPhone endpoint will look like:

```text
http://YOUR_MAC_IP:8000/health-data
```

Check the server is awake:

```text
http://YOUR_MAC_IP:8000/health
```

## Shortcut Payload

The receiver expects a simple JSON dictionary. Start with only a few fields:

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

In iPhone Shortcuts, create a shortcut like this:

1. Add `Current Date`.
2. Format Date as `yyyy-MM-dd`.
3. Add `Find Health Samples` for each metric you care about, such as Steps and Active Energy.
4. Use a statistics action where needed, such as sum for Steps and Active Energy.
5. Add `Dictionary`.
6. Add fields such as:
   - `date`: formatted date
   - `steps`: steps total
   - `active_energy_kcal`: active energy total
   - `exercise_minutes`: exercise minutes total
   - `avg_heart_rate`: average heart rate
   - `sleep_hours`: sleep duration
7. Add `Get Contents of URL`.
8. URL: `http://YOUR_MAC_IP:8000/health-data`
9. Method: `POST`
10. Request Body: `JSON`
11. JSON body: the Dictionary from step 5.

Run it once manually first. If it works, `data/apple_health_daily.csv` will appear locally.

## Automation

For a low-friction local setup:

1. Keep the Mac awake in the evening.
2. Run `python3 health_receiver.py`.
3. In Shortcuts Automation, run the health sync shortcut at night, for example 23:30.
4. Turn off `Ask Before Running`.

If you are away from home at that time, the shortcut may fail. The data is still in Apple Health, so you can run the shortcut manually later when you are home.

## Privacy

The generated files are ignored by Git:

- `data/apple_health_daily.csv`
- `data/raw_health_payloads/`

Do not commit these files unless you intentionally want personal health data in the repository.

# Google Form Setup

Use `google_form_creator.gs` to create a fresh Google Form and linked Google Sheet. The form records one gym session per submission, with up to 6 exercise blocks.

The form has an optional `Date` field. If you leave it blank, the dashboard uses Google Forms' automatic `Timestamp` as the workout date.

The old Google Form responses are preserved in `data/legacy_google_form.csv`. The dashboard reads that file automatically, then reads the new Google Sheet URL you paste into the sidebar.

## Steps

1. Go to https://script.google.com.
2. Create a new project.
3. Paste the contents of `google_form_creator.gs`.
4. Run `createTrainingLabForm`.
5. Approve the Google permissions.
6. Open the logs to get:
   - Form submit URL
   - Response sheet URL
7. Share the new response sheet as `Anyone with the link can view`.
8. Paste the new response sheet URL into the dashboard sidebar.
9. For Streamlit Community Cloud, add the same URL as a secret named `google_sheet_url` so the deployed app remembers it.

## Connect To The Dashboard

Once responses exist, paste the new response sheet URL into the dashboard sidebar. A normal Google Sheets edit URL is fine; the app converts it to CSV internally.

The sheet must be readable by Streamlit. Use one of these options:

- Share the sheet as `Anyone with the link can view`
- Or use `File > Share > Publish to web`

Useful Google Sheets CSV format:

```text
https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/export?format=csv&gid=SHEET_GID
```

The dashboard maps the Google Form column names into its internal workout schema. For the 6-exercise form, the raw sheet is wide format, and the app converts each filled exercise block into long-format per-exercise rows before calculating charts.

The new form's exercise dropdown is grouped with labels like `Push / Bench press` and `Pull / Lat pulldown` so it is easier to scan on a phone. The app strips the group prefix and stores the clean exercise name.

For bench press and incline bench press, selecting `per side` means the dashboard calculates load as `20kg bar + 2 x entered side weight`. For machine or dumbbell-style entries, `per side` or `per hand` is treated as `2 x entered weight`.

If you submit `Later update only` with no exercises, the app creates a zero-set `Session update` row. This lets you add body weight, protein, calories, heart rate, or notes later without disrupting the workout logging flow.

Older entries that used `Other exercise` are detected by keyword. For example:

- `inclined bench` -> `Incline bench press`
- `hammer curl` -> `Hammer curl`
- `leg press calves` -> `Leg press calf raise`
- `stationary bike` -> `Stationary bike`

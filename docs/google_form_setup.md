# Google Form Setup

Use `google_form_creator.gs` to create a Google Form and linked Google Sheet. The form records one gym session per submission, with up to 6 exercise blocks.

## Steps

1. Go to https://script.google.com.
2. Create a new project.
3. Paste the contents of `google_form_creator.gs`.
4. Run `createTrainingLabForm`.
5. Approve the Google permissions.
6. Open the logs to get:
   - Form submit URL
   - Response sheet URL

## Connect To The Dashboard

Once responses exist, publish or export the response sheet as CSV and paste the CSV URL into the dashboard sidebar.

The sheet must be readable by Streamlit. Use one of these options:

- Share the sheet as `Anyone with the link can view`
- Or use `File > Share > Publish to web`

Useful Google Sheets CSV format:

```text
https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/export?format=csv&gid=SHEET_GID
```

The dashboard maps the Google Form column names into its internal workout schema. For the 6-exercise form, it converts each filled exercise block into a normal per-exercise row before calculating charts.

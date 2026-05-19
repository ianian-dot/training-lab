# Google Form Setup

Use `google_form_creator.gs` to create a Google Form and linked Google Sheet.

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

Useful Google Sheets CSV format:

```text
https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/export?format=csv&gid=SHEET_GID
```

The dashboard maps the Google Form column names into its internal workout schema.

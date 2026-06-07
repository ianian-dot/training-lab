const SHEET_NAME = 'Health Daily';
const OPTIONAL_TOKEN = '';

const HEADERS = [
  'date',
  'steps',
  'active_energy_kcal',
  'exercise_minutes',
  'stand_hours',
  'distance_km',
  'resting_heart_rate',
  'avg_heart_rate',
  'sleep_hours',
  'deep_sleep_hours',
  'rem_sleep_hours',
  'source',
  'received_at'
];

function doGet() {
  return jsonResponse({
    status: 'ok',
    message: 'Training Lab Apple Health receiver is running.'
  });
}

function doPost(e) {
  try {
    const payload = parsePayload(e);
    if (OPTIONAL_TOKEN && payload.token !== OPTIONAL_TOKEN) {
      return jsonResponse({ status: 'error', message: 'Invalid token.' });
    }

    const sheet = getHealthSheet();
    const row = normalizePayload(payload);
    upsertByDate(sheet, row);

    return jsonResponse({
      status: 'success',
      saved_date: row.date,
      sheet_url: SpreadsheetApp.getActiveSpreadsheet().getUrl()
    });
  } catch (error) {
    return jsonResponse({
      status: 'error',
      message: String(error)
    });
  }
}

function parsePayload(e) {
  if (!e || !e.postData || !e.postData.contents) {
    throw new Error('No JSON body received.');
  }
  return JSON.parse(e.postData.contents);
}

function getHealthSheet() {
  const spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = spreadsheet.getSheetByName(SHEET_NAME);
  if (!sheet) {
    sheet = spreadsheet.insertSheet(SHEET_NAME);
  }

  const firstRow = sheet.getRange(1, 1, 1, HEADERS.length).getValues()[0];
  const hasHeaders = firstRow.some(value => String(value).trim() !== '');
  if (!hasHeaders) {
    sheet.getRange(1, 1, 1, HEADERS.length).setValues([HEADERS]);
  }
  return sheet;
}

function normalizePayload(payload) {
  const now = new Date();
  const date = firstFilled(payload.date, payload.day, Utilities.formatDate(now, Session.getScriptTimeZone(), 'yyyy-MM-dd'));
  return {
    date: formatDateValue(date),
    steps: numberOrBlank(firstFilled(payload.steps, payload.step_count, payload.stepCount)),
    active_energy_kcal: numberOrBlank(firstFilled(payload.active_energy_kcal, payload.activeEnergy, payload.active_energy, payload.active_calories, payload.calories)),
    exercise_minutes: numberOrBlank(firstFilled(payload.exercise_minutes, payload.exerciseTime, payload.apple_exercise_minutes)),
    stand_hours: numberOrBlank(firstFilled(payload.stand_hours, payload.standHours)),
    distance_km: numberOrBlank(firstFilled(payload.distance_km, payload.walking_running_distance_km, payload.distance)),
    resting_heart_rate: numberOrBlank(firstFilled(payload.resting_heart_rate, payload.restingHeartRate, payload.resting_hr)),
    avg_heart_rate: numberOrBlank(firstFilled(payload.avg_heart_rate, payload.average_heart_rate, payload.averageHeartRate, payload.avg_hr)),
    sleep_hours: numberOrBlank(firstFilled(payload.sleep_hours, payload.sleep)),
    deep_sleep_hours: numberOrBlank(firstFilled(payload.deep_sleep_hours, payload.deepSleep, payload.deep_sleep)),
    rem_sleep_hours: numberOrBlank(firstFilled(payload.rem_sleep_hours, payload.remSleep, payload.rem_sleep)),
    source: firstFilled(payload.source, 'iphone_shortcuts'),
    received_at: now.toISOString()
  };
}

function upsertByDate(sheet, row) {
  const values = sheet.getDataRange().getValues();
  const dateColumnIndex = 0;
  let targetRow = values.length + 1;

  for (let index = 1; index < values.length; index++) {
    const existingDate = formatDateValue(values[index][dateColumnIndex]);
    if (existingDate === row.date) {
      targetRow = index + 1;
      break;
    }
  }

  const output = HEADERS.map(header => row[header]);
  sheet.getRange(targetRow, 1, 1, HEADERS.length).setValues([output]);
}

function firstFilled() {
  for (let index = 0; index < arguments.length; index++) {
    const value = arguments[index];
    if (value !== null && value !== undefined && String(value).trim() !== '') {
      return value;
    }
  }
  return '';
}

function numberOrBlank(value) {
  if (value === null || value === undefined || String(value).trim() === '') {
    return '';
  }
  const number = Number(String(value).replace(',', ''));
  return Number.isNaN(number) ? value : number;
}

function formatDateValue(value) {
  if (Object.prototype.toString.call(value) === '[object Date]' && !Number.isNaN(value.getTime())) {
    return Utilities.formatDate(value, Session.getScriptTimeZone(), 'yyyy-MM-dd');
  }

  const parsed = new Date(value);
  if (!Number.isNaN(parsed.getTime())) {
    return Utilities.formatDate(parsed, Session.getScriptTimeZone(), 'yyyy-MM-dd');
  }

  return String(value);
}

function jsonResponse(data) {
  return ContentService
    .createTextOutput(JSON.stringify(data))
    .setMimeType(ContentService.MimeType.JSON);
}

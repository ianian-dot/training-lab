function createTrainingLabForm() {
  const exercises = [
    'Bench press',
    'Seated lateral raise machine',
    'Barbell bicep curl',
    'Dumbbell bicep curl',
    'Single-arm shoulder raise',
    'Seated shoulder press',
    'Lat pulldown',
    'Seated row',
    'Tricep pulldown',
    'Overhead dumbbell tricep extension',
    'Pull-up',
    'Rear delt machine',
    'Leg extension',
    'Incline T-bar row',
    'Cycling',
    'Other'
  ];

  const muscleGroups = [
    'Chest',
    'Back',
    'Shoulders',
    'Biceps',
    'Triceps',
    'Legs',
    'Core',
    'Cardio',
    'Full body'
  ];

  const form = FormApp.create('Training Lab Workout Log');
  form.setDescription('Submit one response per exercise. Required fields are intentionally quick for gym use.');
  form.setCollectEmail(false);

  form.addDateItem().setTitle('Date').setRequired(true);
  form.addTimeItem().setTitle('Start time');

  form.addListItem()
    .setTitle('Session')
    .setChoiceValues(['Upper', 'Push', 'Pull', 'Legs', 'Arms', 'Full body', 'Other']);

  form.addListItem()
    .setTitle('Exercise')
    .setChoiceValues(exercises)
    .setRequired(true);

  form.addTextItem().setTitle('Other exercise');

  form.addListItem()
    .setTitle('Muscle group')
    .setChoiceValues(muscleGroups)
    .setRequired(true);

  form.addTextItem().setTitle('Sets').setRequired(true);
  form.addTextItem().setTitle('Reps').setRequired(true);
  form.addTextItem().setTitle('Weight kg').setRequired(true);

  form.addListItem()
    .setTitle('Weight basis')
    .setChoiceValues(['total', 'per hand', 'per side', 'bodyweight'])
    .setRequired(true);

  form.addScaleItem().setTitle('RPE').setBounds(1, 10);
  form.addTextItem().setTitle('Duration min');
  form.addTextItem().setTitle('Calories');
  form.addTextItem().setTitle('Avg heart rate');
  form.addTextItem().setTitle('Max heart rate');
  form.addTextItem().setTitle('Body weight kg');

  form.addMultipleChoiceItem()
    .setTitle('Protein taken')
    .setChoiceValues(['Yes', 'No']);

  form.addTextItem().setTitle('Protein grams');
  form.addScaleItem().setTitle('Energy').setBounds(1, 10);
  form.addScaleItem().setTitle('Motivation').setBounds(1, 10);
  form.addScaleItem().setTitle('Session quality').setBounds(1, 10);
  form.addScaleItem().setTitle('Productivity').setBounds(1, 10);
  form.addTextItem().setTitle('Sleep hours');
  form.addParagraphTextItem().setTitle('Feeling');
  form.addParagraphTextItem().setTitle('Notes');

  const sheet = SpreadsheetApp.create('Training Lab Workout Responses');
  form.setDestination(FormApp.DestinationType.SPREADSHEET, sheet.getId());

  Logger.log('Form edit URL: ' + form.getEditUrl());
  Logger.log('Form submit URL: ' + form.getPublishedUrl());
  Logger.log('Response sheet URL: ' + sheet.getUrl());
}

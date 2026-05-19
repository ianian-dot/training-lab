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
  form.setDescription('Submit one response per gym session. Fill each exercise block as you finish it. Leave unused blocks blank.');
  form.setCollectEmail(false);

  form.addDateItem().setTitle('Date').setRequired(true);
  form.addTimeItem().setTitle('Start time');

  form.addListItem()
    .setTitle('Session')
    .setChoiceValues(['Upper', 'Push', 'Pull', 'Legs', 'Arms', 'Full body', 'Cardio', 'Other']);

  for (let index = 1; index <= 6; index++) {
    form.addPageBreakItem().setTitle('Exercise ' + index);

    form.addListItem()
      .setTitle('Exercise ' + index)
      .setChoiceValues(exercises)
      .setRequired(index === 1);

    form.addTextItem().setTitle('Other exercise ' + index);

    form.addListItem()
      .setTitle('Muscle group ' + index)
      .setChoiceValues(muscleGroups);

    form.addTextItem()
      .setTitle('Sets ' + index)
      .setHelpText('Example: 4 or 3.5')
      .setRequired(index === 1);

    form.addTextItem()
      .setTitle('Reps ' + index)
      .setHelpText('Use one number for now. Example: 10')
      .setRequired(index === 1);

    form.addTextItem()
      .setTitle('Weight kg ' + index)
      .setHelpText('Use the number you want to track consistently.')
      .setRequired(index === 1);

    form.addListItem()
      .setTitle('Weight basis ' + index)
      .setChoiceValues(['total', 'per hand', 'per side', 'bodyweight']);

    form.addScaleItem().setTitle('RPE ' + index).setBounds(1, 10);
    form.addParagraphTextItem().setTitle('Exercise notes ' + index);
  }

  form.addPageBreakItem().setTitle('Session details');
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
  form.addParagraphTextItem().setTitle('Session notes');

  const sheet = SpreadsheetApp.create('Training Lab Workout Responses');
  form.setDestination(FormApp.DestinationType.SPREADSHEET, sheet.getId());

  Logger.log('Form edit URL: ' + form.getEditUrl());
  Logger.log('Form submit URL: ' + form.getPublishedUrl());
  Logger.log('Response sheet URL: ' + sheet.getUrl());
}

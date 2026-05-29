function createTrainingLabForm() {
  const exercises = [
    'Push / Bench press',
    'Push / Incline bench press',
    'Push / Seated shoulder press',
    'Push / Seated lateral raise machine',
    'Push / Single-arm shoulder raise',
    'Push / Tricep pulldown',
    'Push / Overhead dumbbell tricep extension',
    'Pull / Lat pulldown',
    'Pull / Seated row',
    'Pull / Incline T-bar row',
    'Pull / Pull-up',
    'Pull / Rear delt machine',
    'Pull / Barbell bicep curl',
    'Pull / Dumbbell bicep curl',
    'Pull / Hammer curl',
    'Legs / Leg extension',
    'Legs / Leg press',
    'Legs / Leg press calf raise',
    'Cardio / Cycling',
    'Cardio / Stationary bike',
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

  const form = FormApp.create('Training Lab Workout Log V2');
  form.setDescription('Submit one response per gym session. Fill each exercise block as you finish it. Leave unused blocks blank. Use Later update only for body weight, protein, or notes after the workout.');
  form.setCollectEmail(false);

  form.addMultipleChoiceItem()
    .setTitle('Entry type')
    .setChoiceValues(['Workout session', 'Later update only'])
    .setRequired(true);

  form.addDateItem()
    .setTitle('Date')
    .setHelpText('Optional. Leave blank to use the automatic submission timestamp.');
  form.addTimeItem().setTitle('Start time');

  form.addListItem()
    .setTitle('Session')
    .setChoiceValues(['Upper', 'Push', 'Pull', 'Legs', 'Arms', 'Full body', 'Cardio', 'Other']);

  for (let index = 1; index <= 6; index++) {
    form.addPageBreakItem().setTitle('Exercise ' + index);

    form.addListItem()
      .setTitle('Exercise ' + index)
      .setChoiceValues(exercises);

    form.addTextItem().setTitle('Other exercise ' + index);

    form.addListItem()
      .setTitle('Muscle group ' + index)
      .setChoiceValues(muscleGroups);

    form.addTextItem()
      .setTitle('Sets ' + index)
      .setHelpText('Example: 4 or 3.5');

    form.addTextItem()
      .setTitle('Reps ' + index)
      .setHelpText('Use one number for now. Example: 10');

    form.addTextItem()
      .setTitle('Weight kg ' + index)
      .setHelpText('Use the number you want to track consistently.');

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

function createTrainingLabSportsForm() {
  const startHours = ['08', '09', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', '23'];
  const startMinutes = ['00', '15', '30', '45'];

  const form = FormApp.create('Training Lab Sports Log');
  form.setDescription('Submit one response whenever you play pickleball or football. This is separate from gym lifting because the metrics are session-based rather than sets/reps/load.');
  form.setCollectEmail(false);

  form.addDateItem()
    .setTitle('Date')
    .setHelpText('Optional. Leave blank to use the automatic submission timestamp.');

  form.addListItem()
    .setTitle('Start hour (24h)')
    .setHelpText('Use 24-hour time. Example: 15 for 3pm, 20 for 8pm.')
    .setChoiceValues(startHours);

  form.addListItem()
    .setTitle('Start minute')
    .setChoiceValues(startMinutes);

  form.addMultipleChoiceItem()
    .setTitle('Sport')
    .setChoiceValues(['Pickleball', 'Football'])
    .setRequired(true);

  form.addTextItem()
    .setTitle('Duration min')
    .setHelpText('Total time playing, including short breaks if useful.');

  form.addScaleItem()
    .setTitle('Intensity')
    .setBounds(1, 10)
    .setHelpText('1 = easy, 10 = extremely hard.');

  form.addScaleItem()
    .setTitle('Session quality')
    .setBounds(1, 10);

  form.addScaleItem()
    .setTitle('Energy')
    .setBounds(1, 10);

  form.addScaleItem()
    .setTitle('Mood after')
    .setBounds(1, 10);

  form.addTextItem().setTitle('Calories');
  form.addTextItem().setTitle('Avg heart rate');
  form.addTextItem().setTitle('Max heart rate');
  form.addTextItem().setTitle('Body weight kg');

  form.addCheckboxItem()
    .setTitle('Body parts that felt worked')
    .setChoiceValues(['Calves', 'Quads', 'Hamstrings', 'Glutes', 'Hip flexors', 'Core', 'Shoulders', 'Forearms', 'Cardio']);

  form.addCheckboxItem()
    .setTitle('Soreness or niggles')
    .setChoiceValues(['None', 'Ankle', 'Knee', 'Hip', 'Hamstring', 'Calf', 'Lower back', 'Shoulder', 'Elbow/wrist']);

  form.addTextItem()
    .setTitle('Score or result')
    .setHelpText('Optional. Example: won 11-8, casual rally, 5-a-side draw.');

  form.addParagraphTextItem()
    .setTitle('Notes')
    .setHelpText('Anything useful: court/field, partners, movement felt sharp/sluggish, injuries, weather.');

  const sheet = SpreadsheetApp.create('Training Lab Sports Responses');
  form.setDestination(FormApp.DestinationType.SPREADSHEET, sheet.getId());

  Logger.log('Sports form edit URL: ' + form.getEditUrl());
  Logger.log('Sports form submit URL: ' + form.getPublishedUrl());
  Logger.log('Sports response sheet URL: ' + sheet.getUrl());
}

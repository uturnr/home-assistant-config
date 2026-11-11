import hass_plus


class HomeAwayService(hass_plus.HassPlus):
  def initialize(self):
    self.log('🐣 Listening for persons in zone.home.')
    self.listen_state(
      self.persons_home_changed,
      'zone.home',
      attribute='persons',
    )

  def persons_home_changed(self, entity, attribute, old, new, kwargs):
    old_count = len(old or [])
    new_count = len(new or [])
    self.log(f'📍 Persons home: {old_count} → {new_count}')

    if old_count == 0 and new_count > 0:
      self.handle_home()
    elif old_count > 0 and new_count == 0:
      self.handle_away()

  def handle_home(self):
    if self.get_state('input_boolean.arrive_home_enabled') != 'on':
      self.log('📍 Home - arrive_home_enabled is off, skipping.')
      return
    self.log('📍 Home - turn on lights, music, glass transparency')

    # Set appropriate lighting scene based on time
    if self.now_is_between('07:00:00', '19:00:00'):
      self.turn_on('scene.day_lights')
      self.turn_on('scene.privacy_off')
    else:
      self.turn_on('scene.night_lights')

    if not self.now_is_between('00:00:00', '10:00:00'):
      self.call_service('script/radioparadise_tv')

  def turn_on_away_lights(self, kwargs={}):
    self.turn_on('scene.away_lights')

  def handle_away(self):
    if self.get_state('input_boolean.leave_home_enabled') != 'on':
      self.log('📍 Away - leave_home_enabled is off, skipping.')
      return
    self.log(
      '📍 Away - turn off indoor lights, turn on fan light, frost glass.'
    )
    self.turn_off('light.indoor_lights')
    self.turn_on('scene.privacy')
    self.run_in(
      self.turn_on_away_lights,
      5,
    )

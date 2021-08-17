import appdaemon.plugins.hass.hassapi as hass

#
# Home/Away Service
#
# Args:
#

class HomeAwayService(hass.Hass):
  def initialize(self):
    self.log('🐣 Listening for zone changes.', ascii_encode=False)
    self.listen_state(self.zone_changed, 'person.me')

  def zone_changed(self, entity, attribute, old, new, kwargs):
    self.log(f"Zone changed to {new}.")
    if new == 'home':
      self.handle_home()
    elif new == 'not_home':
      self.handle_away()

  def handle_home(self):
    self.log('Home - turn on lights.')
    self.call_service('light/turn_on', entity_id = 'light.west_lights')
    self.call_service('light/turn_on', entity_id = 'light.living_room_lights')
    if not self.now_is_between('08:00:00', '10:00:00'):
      self.call_service('script/accuradio_tv')

  def handle_away(self):
    self.log('Home - turn off indoor, turn on fan.')
    self.call_service('light/turn_off', entity_id = 'light.indoor_lights')
    self.call_service('light/turn_on', entity_id = 'light.fan_light')

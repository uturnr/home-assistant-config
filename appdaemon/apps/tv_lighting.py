import appdaemon.plugins.hass.hassapi as hass

class TvLighting(hass.Hass):

  def initialize(self):
    # self.couch_light_status = self.get_state('light.couch_light')

    self.listen_state(
      self.handle_tv_status_change,
      'media_player.living_room_tv'
    )

    # self.listen_state(
    #   self.handle_couch_light_toggled,
    #   'light.couch_light'
    # )
  

  # def handle_couch_light_toggled(self, entity, attribute, old, new):
  #   if self.get_state('media_player.living_room_tv') == ''

  def handle_tv_status_change(self, entity, attribute, old, new, kwargs):
    if new == 'playing':
      self.call_service(
        'light/turn_off',
        entity_id = 'light.couch_light'
      )
    else:
      self.call_service(
        'light/turn_on',
        entity_id = 'light.couch_light'
      )

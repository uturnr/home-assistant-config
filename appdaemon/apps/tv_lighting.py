import appdaemon.plugins.hass.hassapi as hass

class TvLighting(hass.Hass):
  SOURCES_FOR_LIGHTING_CHANGES = [
    'Global TV',
    'Google Play Movies & TV',
    'Netflix',
    'Plex - Stream for Free',
    'Prime Video',
    'Roku Media Player',
    'Web Video Caster - Receiver',
    'YouTube'
  ]

  def initialize(self):
    self.listen_state(
      self.handle_tv_change,
      'media_player.living_room_tv',
      attribute = 'all'
    )
  
  def check_source_should_affect_lighting(self, source):
    return source in self.SOURCES_FOR_LIGHTING_CHANGES
  
  def handle_tv_change(self, entity, attribute, old, new, kwargs):
    old_state = old['state']
    new_state = new['state']
    old_source = old['attributes']['source']
    new_source = new['attributes']['source']

    # Turn the light off when playing.
    if (new_state == 'playing'):
      self.handle_tv_started_playing(new_source)
    # Turn the light on when done watching.
    elif (
      new_state != 'paused' and
      (
        old_state == 'playing' or
        old_state == 'paused'
      )
    ):
      self.handle_tv_stopped_playing(old_source)
      

  def handle_tv_started_playing(self, new_source):
    if (
      self.check_source_should_affect_lighting(new_source) and
      self.get_state('light.couch_light') == 'on'
    ):
      self.call_service(
        'light/turn_off',
        entity_id = 'light.couch_light'
      )

  def handle_tv_stopped_playing(self, old_source):
    if (
      self.check_source_should_affect_lighting(old_source) and
      self.get_state('light.wall_lights') == 'on' and
      self.get_state('light.couch_light') == 'off'
    ):
      self.call_service(
        'light/turn_on',
        entity_id = 'light.couch_light'
      )


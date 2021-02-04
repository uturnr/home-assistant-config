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
      self.handle_tv_started_playing,
      'media_player.living_room_tv',
      new = 'playing'
    )

    self.listen_state(
      self.handle_tv_stopped_playing,
      'media_player.living_room_tv',
      old = 'playing',
      duration = 60
    )
  
  def check_source_should_affect_lighting(self):
    current_source = self.get_state(
      'media_player.living_room_tv',
      attribute = 'source'
    )
    return current_source in self.SOURCES_FOR_LIGHTING_CHANGES

  def handle_tv_started_playing(self, entity, attribute, old, new, kwargs):
    if (
      self.check_source_should_affect_lighting() and
      self.get_state('light.couch_light') == 'on'
    ):
      self.call_service(
        'light/turn_off',
        entity_id = 'light.couch_light'
      )

  def handle_tv_stopped_playing(self, entity, attribute, old, new, kwargs):
    if (
      self.check_source_should_affect_lighting() and
      self.get_state('light.wall_lights') == 'on' and
      self.get_state('light.couch_light') == 'off'
    ):
      self.call_service(
        'light/turn_on',
        entity_id = 'light.couch_light'
      )


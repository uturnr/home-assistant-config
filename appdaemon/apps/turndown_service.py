import hass_plus
import datetime

#
# Turndown Service
#
# Args:
#

class TurndownService(hass_plus.HassPlus):
  LIGHTS = 'light.non_kitchen_main_lights'

  def initialize(self):
    pass

  def start_advice(self):
    if self.get_state('input_boolean.turndown_advice') == 'on':
      self.log('Running Turndown Advice')
      # TODO

  # No transition support with Tuya bulbs. Immediately dim instead.
  def dim_lights(self):
    if (
      self.get_state('input_boolean.turndown_lights') == 'on' and
      self.get_state(self.LIGHTS) == 'on'
    ):
      self.log('🌝 Dimming Lights')
      self.adjust_lights(self.LIGHTS, None, 370)

  def handle_bedtime(self):
    self.log('Running Bedtime Tasks')
    # TV Off
    if self.get_state('input_boolean.turndown_tv') == 'on':
      self.log('Turning off TV')
      self.call_service(
        'media_player/turn_off',
        entity_id = 'media_player.living_room_tv'
      )
    # Lights very dim
    if (
      self.get_state('input_boolean.turndown_lights') == 'on' and
      self.get_state(self.LIGHTS)  == 'on'
    ):
      self.log('Dimming Lights More')
      self.call_service(
        'light/turn_on',
        entity_id = self.LIGHTS,
        brightness = 1,
        color_temp = 370
      )

  def handle_minute_changed(self, current_time_str):
    turndown_enabled = self.get_state('input_boolean.turndown_enabled')
    turndown_lights_duration = int(float(self.get_state('input_number.turndown_lights_duration')))
    turndown_advice_timedelta = int(float(self.get_state('input_number.turndown_advice_timedelta')))
    me_state = self.get_state('person.me')
    bedtime_str = self.get_state('input_datetime.bedtime')
    bedtime = self.datetime().strptime(bedtime_str, '%H:%M:%S')
    turndown_lights_start_time = bedtime - datetime.timedelta(minutes=turndown_lights_duration)
    turndown_lights_start_time_str = turndown_lights_start_time.strftime("%H:%M:00")
    turndown_advice_time = bedtime - datetime.timedelta(minutes=turndown_advice_timedelta)
    turndown_advice_time_str = turndown_advice_time.strftime("%H:%M:00")

    turndown_weekend = self.get_state('input_boolean.turndown_weekend')
    current_day_of_week = str(self.date().isoweekday())
    if current_day_of_week in '1,2,3,4,5':
      is_weekday = True
    else:
      is_weekday = False

    # Check if should run wakeup actions
    if (
      me_state == 'home' and
      turndown_enabled == 'on' and (
        is_weekday or
        turndown_weekend == 'on'
      )
    ):
      if (current_time_str == turndown_advice_time_str):
        self.start_advice()
      if (current_time_str == turndown_lights_start_time_str):
        self.dim_lights(turndown_lights_duration)
      if (current_time_str == bedtime_str):
        self.handle_bedtime()

import hass_plus
import datetime

#
# Turndown Service
#
# Args:
#


class TurndownService(hass_plus.HassPlus):
  # Use a light or light group to determine if the main lights are on
  LIGHTS = 'light.fan_bulb_2'

  def initialize(self):
    pass

  def start_advice(self):
    if self.get_state('input_boolean.turndown_advice') == 'on':
      self.log('🌝 Running Turndown Advice')
      # TODO

  # No transition support with Tuya bulbs. Immediately dim instead.
  def dim_lights(self):
    if (
      self.get_state('input_boolean.turndown_lights') == 'on'
      and self.get_state(self.LIGHTS) == 'on'
    ):
      self.log('🌝 Activating Night Lights')
      self.turn_on('scene.night_lights')

  def start_sleep_curve(self):
    if (
      self.get_state('input_boolean.turndown_sleep_curve') == 'on'
      and self.get_state('input_boolean.sleep_curve_enabled') == 'off'
    ):
      self.log('🌝 Activating Sleep Curve')
      self.turn_on('input_boolean.sleep_curve_enabled')

  def handle_bedtime(self):
    self.log('🌝 Running Bedtime Tasks')
    # TV Off
    if self.get_state('input_boolean.turndown_tv') == 'on':
      self.log('🌝 Turning off TV')
      self.turn_off('media_player.living_room_tv')
    # Lights very dim
    if (
      self.get_state('input_boolean.turndown_lights') == 'on'
      and self.get_state(self.LIGHTS) == 'on'
    ):
      self.log('🌝 Activating Go to Bed Lights')
      self.turn_on('scene.go_to_bed_lights')

  def handle_minute_changed(self, current_time_str):
    turndown_enabled = self.get_state('input_boolean.turndown_enabled')
    me_state = self.get_state('person.me')
    bedtime_str = self.get_state('input_datetime.bedtime')
    bedtime = self.datetime().strptime(bedtime_str, '%H:%M:%S')

    turndown_lights_pre = int(float(
      self.get_state('input_number.turndown_lights_pre'))
    )
    turndown_lights_time = bedtime - datetime.timedelta(
      minutes=turndown_lights_pre
    )
    turndown_lights_time_str = turndown_lights_time.strftime("%H:%M:00")

    turndown_sleep_curve_pre = int(float(
      self.get_state('input_number.turndown_sleep_curve_pre'))
      )
    turndown_sleep_curve_time = bedtime - datetime.timedelta(
      minutes=turndown_sleep_curve_pre
    )
    turndown_sleep_curve_time_str = turndown_sleep_curve_time.strftime(
      "%H:%M:00"
    )

    turndown_weekend = self.get_state('input_boolean.turndown_weekend')
    current_day_of_week = str(self.date().isoweekday())
    if current_day_of_week in '1,2,3,4,5':
      is_weekday = True
    else:
      is_weekday = False

    # Check if should run turndown actions
    if (
      me_state == 'home'
      and turndown_enabled == 'on' and (
        is_weekday
        or turndown_weekend == 'on'
      )
    ):
      # if (current_time_str == turndown_advice_time_str):
      #   self.start_advice()
      if (current_time_str == turndown_lights_time_str):
        self.dim_lights()

      if (current_time_str == bedtime_str):
        self.handle_bedtime()

    # Run sleep curve even if I'm not home. TODO: Consider skipping if I have
    # not been home for 4 hours.
    if (turndown_enabled == 'on'):
      if (current_time_str == turndown_sleep_curve_time_str):
        self.start_sleep_curve()

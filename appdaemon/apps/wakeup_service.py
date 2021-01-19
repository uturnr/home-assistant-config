import appdaemon.plugins.hass.hassapi as hass
import datetime

#
# Wakeup Service
#
# Args:
#

class WakeupService(hass.Hass):
  SHOWER_HEAT_PRE_MINUTES = 5
  SHOWER_HEAT_POST_MINUTES = 15

  def initialize(self):
    pass

  def start_wakeup(self, wakeup_duration):
    self.log('run start wakeup')
    self.call_service(
      'light/turn_on',
      entity_id = 'light.bedroom_light',
      transition = wakeup_duration * 60,
      brightness = 120
    )

  def start_music(self):
    self.log('run music')
    self.call_service('script/spotify_tv')

  def start_shower_heater(self):
    self.log('run shower heater')
    self.call_service(
      'switch/turn_on',
      entity_id = 'switch.binary_power_switch_instance_2_switch'
    )

  def stop_shower_heater(self):
    self.log('stop shower heater')
    self.call_service(
      'switch/turn_off',
      entity_id = 'switch.binary_power_switch_instance_2_switch'
    )

  def handle_minute_changed(self, current_time_str):
    wakeup_enabled = self.get_state('input_boolean.wakeup_enabled')
    wakeup_duration = int(float(self.get_state('input_number.wakeup_duration')))
    me_state = self.get_state('person.me')
    wakeup_time_str = self.get_state('input_datetime.wakeup_time')
    wakeup_time = self.datetime().strptime(wakeup_time_str, '%H:%M:%S')
    wakeup_start_time = wakeup_time - datetime.timedelta(minutes=wakeup_duration)
    wakeup_start_time_str = wakeup_start_time.strftime("%H:%M:00")
    shower_heater_start_time = wakeup_time - datetime.timedelta(
      minutes=self.SHOWER_HEAT_PRE_MINUTES
    )
    shower_heater_start_time_str = shower_heater_start_time.strftime("%H:%M:00")
    shower_heater_end_time = wakeup_time + datetime.timedelta(
      minutes=self.SHOWER_HEAT_POST_MINUTES
    )
    shower_heater_end_time_str = shower_heater_end_time.strftime("%H:%M:00")

    wakeup_weekend = self.get_state('input_boolean.wakeup_weekend')
    current_day_of_week = str(self.date().isoweekday())
    if current_day_of_week in '1,2,3,4,5':
      is_weekday = True
    else:
      is_weekday = False

    # Check if should run wakeup actions
    if (
      me_state == 'home' and
      wakeup_enabled == 'on' and (
        is_weekday or
        wakeup_weekend == 'on'
      )
    ):
      if (current_time_str == wakeup_start_time_str):
        self.start_wakeup(wakeup_duration)
      if (current_time_str == wakeup_time_str):
        self.start_music()
      if (current_time_str == shower_heater_start_time_str):
        self.start_shower_heater()
      if (current_time_str == shower_heater_end_time_str):
        self.stop_shower_heater()

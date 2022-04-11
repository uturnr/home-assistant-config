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

  def handle_minute_changed(self, current_time_str):
    wakeup_enabled = self.get_state('input_boolean.wakeup_enabled')
    lights_pre = int(float(self.get_state('input_number.wakeup_lights_duration_pre')))
    lights_post = int(float(self.get_state('input_number.wakeup_lights_duration_post')))
    music_post = int(float(self.get_state('input_number.wakeup_music_duration_post')))
    lights_duration = lights_pre + lights_post
    me_state = self.get_state('person.me')
    wakeup_time_str = self.get_state('input_datetime.wakeup_time')
    wakeup_time = self.datetime().strptime(wakeup_time_str, '%H:%M:%S')
    lights_start_time = wakeup_time - datetime.timedelta(minutes=lights_pre)
    lights_start_time_str = lights_start_time.strftime("%H:%M:00")
    music_start_time = wakeup_time + datetime.timedelta(minutes=music_post)
    music_start_time_str = music_start_time.strftime("%H:%M:00")
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

    # Check if should run wakeup actions.
    if (
      me_state == 'home' and
      wakeup_enabled == 'on' and (
        is_weekday or
        wakeup_weekend == 'on'
      )
    ):
      if (current_time_str == lights_start_time_str):
        self.start_lights(lights_duration)
      if (
        current_time_str == wakeup_time_str and
        self.get_state('input_boolean.wakeup_all_lights') == 'on'
      ):
        self.turn_on_all_lights()
      if (
        current_time_str == music_start_time_str and
        self.get_state('input_boolean.wakeup_music') == 'on'
      ):
        self.start_music()
      if (
        current_time_str == shower_heater_start_time_str and
        self.get_state('input_boolean.wakeup_shower_heater') == 'on'
      ):
        self.start_shower_heater()
    
    # Turn off shower heater regardless of options.
    if (current_time_str == shower_heater_end_time_str):
      self.stop_shower_heater()

  def start_lights(self, lights_duration):
    self.log('💡 Starting to fade in lights for wakeup.', ascii_encode=False)
    self.call_service(
      'light/turn_on',
      entity_id = 'light.bedroom_light',
      transition = lights_duration * 60,
      brightness = 120
    )
  
  def turn_on_all_lights(self):
    self.log('💡 Turning on main house lights for wakeup.', ascii_encode=False)
    self.call_service(
      'light/turn_on',
      entity_id = 'light.main_lights',
    )

  def start_music(self):
    self.log('🎵 Starting to play music for wakeup.', ascii_encode=False)
    self.call_service('script/accuradio_tv')

  def start_shower_heater(self):
    self.log('🔥 Starting shower heater for wakeup.', ascii_encode=False)
    self.call_service(
      'switch/turn_on',
      entity_id = 'switch.shower_heater'
    )

  def stop_shower_heater(self):
    self.log('🧯 Stopping shower heater for wakeup.', ascii_encode=False)
    self.call_service(
      'switch/turn_off',
      entity_id = 'switch.shower_heater'
    )

import hass_plus

class SleepCurve(hass_plus.HassPlus):
  CURVE = [
    16,
    16,
    16,
    18,
    18,
    20,
    20,
    22,
    24
  ]
  HOUR_SECONDS = 3600
  CALL_INTERVAL_SECONDS = 10
  POWER_INTERVAL_SECONDS_1 = 60
  POWER_INTERVAL_SECONDS_2 = 300
  MAX_RETRIES = 2
  SANITY_CHECK_MINUTES = 4

  def initialize(self):
    # TODO: fix (invalid callback handle) 
    self.handle = None
    self.sanity_check_handle = None
    self.retries = 0
    self.power_retries = 0
    self.sanity_checks = 0
    self.sanity_check_start_temp = None
    self.listen_state(
      self.sleep_curve_changed, 
      'input_boolean.sleep_curve_enabled'
    )

    self.log('🐣 Listening for changes to sleep curve toggle.')

    # Resume by restarting current hour after reboot
    sleep_curve_enabled = self.get_state('input_boolean.sleep_curve_enabled')
    if sleep_curve_enabled:
      hour_number = int(float(self.get_state('input_number.sleep_curve_hour')))
      if hour_number != 0:
        self.set('input_number.sleep_curve_hour', hour_number - 1)
      self.update_temp_and_next()

  def sleep_curve_changed(self, entity, attribute, old, new, kwargs):
    if new == 'on':
      self.sleep_curve_on()
    elif new == 'off':
      self.sleep_curve_off()

  def power_cycle(self):
    self.cancel_timers()

    if self.power_retries == self.MAX_RETRIES:
      self.notify('Sleep Curve', 'Too many power cycle attempts. Giving up.')
    else:
      self.power_retries += 1
      self.turn_off('switch.air_conditioner_power')
      next_delay = self.POWER_INTERVAL_SECONDS_1 if self.power_retries < 2 else self.POWER_INTERVAL_SECONDS_2
        
      self.notify(
        'Sleep Curve',
        f'Power cycling air conditioner and retrying in {next_delay} seconds'
      )

      self.handle = self.run_in(
        self.set_ac_power_to_on_and_next,
        next_delay
      )
    
  def set_ac_power_to_on_and_next(self, kwargs={}):
    ac_power_on: bool = self.get_state('switch.air_conditioner_power') == 'on'

    if not ac_power_on:
      self.turn_on('switch.air_conditioner_power')
      self.notify('Sleep Curve', 'AC Power turn on attempted.')
      next_delay = self.CALL_INTERVAL_SECONDS
    else:
      self.log('🎛 AC Power already on.')
      next_delay = 0

    self.log(f'🎛 Setting AC to cool in {next_delay} seconds.')

    self.handle = self.run_in(
      self.set_ac_to_cool_and_next,
      next_delay
    )

  def set_ac_to_cool_and_next(self, kwargs={}):
    ac_state_cool: bool = self.get_state('climate.bedroom_ac') == 'cool'

    if not ac_state_cool:
      self.call_service(
        'climate/set_hvac_mode',
        entity_id = 'climate.bedroom_ac',
        hvac_mode = 'cool',
      )
      self.log('🎛 AC set to cool mode attempted.')
      next_delay = self.CALL_INTERVAL_SECONDS
    else:
      next_delay = 0
    
    self.handle = self.run_in(
      self.ac_to_cool_check_and_next,
      next_delay
    )
  
  def ac_to_cool_check_and_next(self, kwargs={}):
    ac_state_cool: bool = self.get_state('climate.bedroom_ac') == 'cool'
    next_delay = self.CALL_INTERVAL_SECONDS

    if not ac_state_cool and self.retries == self.MAX_RETRIES:
      self.power_cycle()
    elif not ac_state_cool:
      self.retries += 1
      self.notify(
        'Sleep Curve',
        f'AC failed to set cool mode. Will retry. ({self.retries})'
      )
      self.handle = self.run_in(
        self.set_ac_to_cool_and_next,
        next_delay
      )
    else:
      self.retries = 0
      self.log('🎛 AC set to cool mode successful.')
      self.log(f'🎛 Setting AC fan to auto in {next_delay} seconds.')
      self.handle = self.run_in(
        self.set_ac_fan_to_auto_and_next,
        next_delay
      )

  def set_ac_fan_to_auto_and_next(self, kwargs={}):
    ac_fan_state_auto: bool = self.get_state(
      'climate.bedroom_ac',
      'fan_mode'
    ) == 'Auto'

    if not ac_fan_state_auto:
      self.call_service(
        'climate/set_fan_mode',
        entity_id = 'climate.bedroom_ac',
        fan_mode = 'Auto',
      )
      self.log('🎛 AC set to auto fan mode attempted.')
      next_delay = self.CALL_INTERVAL_SECONDS
    else:
      next_delay = 0

    self.handle = self.run_in(
      self.ac_fan_to_auto_check_and_next,
      next_delay
    )

  def ac_fan_to_auto_check_and_next(self, kwargs={}):
    ac_fan_state_auto: bool = self.get_state(
      'climate.bedroom_ac',
      'fan_mode'
    ) == 'Auto'
    next_delay = self.CALL_INTERVAL_SECONDS

    if not ac_fan_state_auto and self.retries == self.MAX_RETRIES:
      self.power_cycle()
    elif not ac_fan_state_auto:
      self.retries += 1
      self.notify(
        'Sleep Curve',
        f'AC failed to set fan mode. Will retry. ({self.retries})'
      )
      self.handle = self.run_in(
        self.set_ac_fan_to_auto_and_next,
        next_delay
      )
    else:
      self.retries = 0
      self.log('🎛 AC set to fan mode auto successful.')
      self.log(f'🎛 Setting AC preset to eco in {next_delay} seconds.')
      self.handle = self.run_in(
        self.set_ac_preset_to_eco_and_next,
        next_delay
      )

  def set_ac_preset_to_eco_and_next(self, kwargs={}):
    ac_preset_eco: bool = self.get_state(
      'climate.bedroom_ac',
      'preset_mode'
    ) == 'eco'

    if not ac_preset_eco:
      self.call_service(
        'climate/set_preset_mode',
        entity_id = 'climate.bedroom_ac',
        preset_mode = 'eco',
      )
      self.log('🎛 AC set to eco mode attempted.')
      next_delay = self.CALL_INTERVAL_SECONDS
    else:
      next_delay = 0

    self.handle = self.run_in(
      self.ac_preset_to_eco_check_and_next,
      next_delay
    )


  def ac_preset_to_eco_check_and_next(self, kwargs={}):
    ac_preset_eco: bool = self.get_state(
      'climate.bedroom_ac',
      'preset_mode'
    ) == 'eco'
    next_delay = self.CALL_INTERVAL_SECONDS

    if not ac_preset_eco and self.retries == self.MAX_RETRIES:
      self.power_cycle()
    elif not ac_preset_eco:
      self.retries += 1
      self.notify(
        'Sleep Curve',
        f'AC failed to set eco mode. Will retry. ({self.retries})'
      )
      self.handle = self.run_in(
        self.set_ac_preset_to_eco_and_next,
        next_delay
      )
    else:
      self.retries = 0
      self.log('🎛 AC set to eco mode successful.')
      self.log(f'🎛 Setting AC temperature in {next_delay} seconds.')
      self.handle = self.run_in(
        self.update_temp_and_next,
        next_delay
      )

  def sleep_curve_on(self):
    self.log('🌙 Sleep Curve starting.')
    self.retries = 0
    self.power_retries = 0

    self.set_ac_power_to_on_and_next()

  def cancel_timers(self):
    if self.handle and self.timer_running(self.handle):
      self.cancel_timer(self.handle)
      self.log('🌙 Sleep Curve main timer canceled.')
    else:
      self.log('🌙 No Sleep Curve main timer to cancel.')
    self.handle = None
    if self.sanity_check_handle and self.timer_running(self.sanity_check_handle):
      self.cancel_timer(self.sanity_check_handle)
      self.log('🌙 Sleep Curve sanity timer canceled.')
    else:
      self.log('🌙 No Sleep Curve sanity timer to cancel.')
    self.sanity_check_handle = None

  def sleep_curve_off(self):
    self.cancel_timers()
    self.log('🌙 Sleep Curve ended. A/C off.')
    self.call_service('climate/turn_off', entity_id='climate.bedroom_ac')
    self.set('input_number.sleep_curve_hour', 0)
    pass

  def update_temp_and_next(self, kwargs={}):
    sleep_curve_enabled = self.get_state('input_boolean.sleep_curve_enabled')
    hour_number = int(float(self.get_state('input_number.sleep_curve_hour')))

    if sleep_curve_enabled == 'off':
      return

    if hour_number < len(self.CURVE):
      # Set the appropriate temperature for the given hour.
      desired_temp = self.CURVE[hour_number]
      self.call_service(
        'climate/set_temperature',
        entity_id='climate.bedroom_ac',
        temperature=desired_temp,
      )
      self.log(
        f'🌙 Sleep Curve has attempted to set temperature to {desired_temp}.'
      )
      self.handle = self.run_in(
        self.update_temp_check_and_next,
        self.CALL_INTERVAL_SECONDS,
      )

    else:
      # If no more temp changes exist, turn off sleep curve.
      self.set('input_boolean.sleep_curve_enabled', 'off')

  def update_temp_check_and_next(self, kwargs={}):
    hour_number = int(float(self.get_state('input_number.sleep_curve_hour')))
    desired_temp = self.CURVE[hour_number]
    temp_correct: bool = self.get_state(
      'climate.bedroom_ac',
      'temperature'
    ) == desired_temp
    next_delay = self.CALL_INTERVAL_SECONDS

    if not temp_correct and self.retries == self.MAX_RETRIES:
      self.notify(
        'Sleep Curve',
        f'AC failed to set temp to {desired_temp} too many times. Giving up.'
      )
    elif not temp_correct:
      self.retries += 1
      self.notify(
        'Sleep Curve',
        f'AC failed to set temp to {desired_temp}. Will retry. ({self.retries})'
      )
      self.handle = self.run_in(
        self.update_temp_and_next,
        next_delay
      )
    else:
      if hour_number == 0:
        self.log(f'🎛 Successfully set initial sleep curve temp to {desired_temp}')
        self.sanity_checks = 0
        self.sanity_check_start_temp = self.get_state(
          'climate.bedroom_ac',
          'current_temperature'
        )
        self.sanity_check_handle = self.run_in(
          self.run_sanity_check_and_next,
          60,
        )
          
      # Increment the hour and set a timer for the next action to run.
      self.set('input_number.sleep_curve_hour', hour_number + 1)
      self.handle = self.run_in(
        self.update_temp_and_next,
        self.HOUR_SECONDS,
      )

  # midea-ac-py will happily "accept" commands and update local state when
  # the wifi on the unit has completely failed and needs a power cycle. (🙄)
  # Watch the temperature for a bit to make sure the unit is actually connected.
  def run_sanity_check_and_next(self, kwargs={}):
    # TODO: check if the actual temp is close to the desired temp. If so,
    # consider the sanity check satisfied.
    current_temp = self.get_state('climate.bedroom_ac', 'current_temperature')

    if current_temp != self.sanity_check_start_temp:
      self.notify(
        'Sleep curve',
        f'🎛 AC actual temperature started at {self.sanity_check_start_temp}'
        + f' and is now {current_temp}. Sanity check complete.'
      )
      return
    
    if self.sanity_checks >= self.SANITY_CHECK_MINUTES:
      self.power_cycle()
    else:
      self.sanity_checks = self.sanity_checks + 1
      self.log(
        f'🎛 AC actual temperature hasn’t changed yet. '
        + f'It has been {self.sanity_checks} minute(s).'
      )
      self.sanity_check_handle = self.run_in(
        self.run_sanity_check_and_next,
        60,
      )

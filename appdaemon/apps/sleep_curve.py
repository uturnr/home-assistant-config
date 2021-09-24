import appdaemon.plugins.hass.hassapi as hass

class SleepCurve(hass.Hass):
  CURVE = [
    16,
    18,
    18,
    19,
    20,
    22,
    24
  ]

  def initialize(self):
    self.log('🐣 Listening for changes to sleep curve toggle.', ascii_encode=False)
    
    # TODO: try get self.utils = utils.Utils() or similar working.
    # Provides type hints
    self.utils = self.get_app('utils')
    
    self.listen_state(
      self.sleep_curve_changed, 
      'input_boolean.sleep_curve_enabled'
    )

    # Resume by jumping to next hour after reboot 
    sleep_curve_enabled = self.get_state('input_boolean.sleep_curve_enabled')
    if sleep_curve_enabled:
      self.run_next_action()

  def sleep_curve_changed(self, entity, attribute, old, new, kwargs):
    if new == 'on':
      self.sleep_curve_on()
    elif new == 'off':
      self.sleep_curve_off()

  def sleep_curve_on(self):
    self.log('🌙 Sleep Curve starting.', ascii_encode=False)

    self.call_service('climate/turn_on', entity_id='climate.bedroom_ac')
    self.call_service(
      'climate/set_hvac_mode',
      entity_id = 'climate.bedroom_ac',
      hvac_mode = 'cool',
    )
    self.call_service(
      'climate/set_fan_mode',
      entity_id = 'climate.bedroom_ac',
      fan_mode = 'Auto',
    )

    self.run_next_action()

  def sleep_curve_off(self):
    self.log('🌙 Sleep Curve ended. A/C off.', ascii_encode=False)
    self.call_service('climate/turn_off', entity_id='climate.bedroom_ac')
    self.utils.set_input('input_number.sleep_curve_hour', 0)
    pass

  def run_next_action(self, kwargs={}):
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
        f'🌙 Sleep Curve has set the temperature to {desired_temp}.',
        ascii_encode=False
      )

      # Increment the hour and set a timer for the next action to run.
      self.utils.set_input('input_number.sleep_curve_hour', hour_number + 1)
      self.run_in(
        self.run_next_action,
        3600,
      )
    else:
      # If no more temp changes exist, turn off sleep curve.
      self.utils.set_input('input_boolean.sleep_curve_enabled', 'off')
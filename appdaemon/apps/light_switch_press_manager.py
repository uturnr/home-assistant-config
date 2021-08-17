import appdaemon.plugins.hass.hassapi as hass

#
# Light Switch Press Manager
#
# Args:
#

class LightSwitchPressManager(hass.Hass):
  # Configured for Red Series dimmer
  ZW_PARAM = 16
  ZW_SET_PARAM = 'zwave_js/bulk_set_partial_config_parameters'
  NOTIF_TRACK_COLOR = 'input_number/set_value'
  NOTIF_OFF = 65792
  SWITCHES = [
    {
      'name': 'Kitchen',
      'entity_id': 'light.kitchen_light',
      'node_id': 8,
      'notification_tracking_number': 'input_number.kitchen_notification',
    }
  ]

  def initialize(self):
    for switch in self.SWITCHES:
      node_id = switch['node_id']

      # Listen for scenes
      self.listen_event(
        self.handle_switch_press,
        'zwave_js_value_notification',
        node_id = node_id,
        switch_name = switch['name'],
        switch_entity_id = switch['entity_id'],
        notification_tracking_number = switch['notification_tracking_number'],
      )

      self.log(f'🐣 Listening for presses on {switch["name"]} (Node ID {node_id}).', ascii_encode=False)
  
  def set_color_tracking(self, tracking_number, color):
    self.call_service(
      self.NOTIF_TRACK_COLOR,
      entity_id = tracking_number,
      value = color
    )
  
  def set_led_color_now(self, entity_id, color):
    self.call_service(
      self.ZW_SET_PARAM,
      entity_id = entity_id,
      parameter = self.ZW_PARAM,
      value = color
    )

  def handle_switch_press(self, event_name, data, kwargs):
    switch_name = kwargs['switch_name']
    switch_entity_id = kwargs['switch_entity_id']
    notification_tracking_number = kwargs['notification_tracking_number']

    pressed = None
    if data['value'] == 'KeyPressed': # Pressed 1 time
      pressed = 1
    elif data['value'] == 'KeyPressed2x': # Pressed 2 times
      pressed = 2
    elif data['value'] == 'KeyPressed3x': # Pressed 3 times
      pressed = 3
    elif data['value'] == 'KeyPressed4x': # Pressed 4 times
      pressed = 4

    up = None
    if data['label'] == 'Scene 002': # Up
      up = True
    elif data['label'] == 'Scene 001': # Down
      up = False

    if pressed == None or up == None:
      return

    self.log(f'🎚 {switch_name} switch pressed {pressed}x {"up" if up else "down"}.', ascii_encode=False)

    if switch_name == 'Kitchen':
      if pressed == 1 and up:
        self.call_service(
          'light/turn_on',
          entity_id = 'light.west_lights'
        )
      elif pressed == 2 and up:
        self.call_service(
          'light/turn_on',
          entity_id = 'light.kitchen_light'
        )
      elif pressed == 3 and up:
        self.call_service(
          'light/turn_on',
          entity_id = 'light.laundry_room_lights'
        )
      elif pressed == 1 and not up:
        self.call_service(
          'light/turn_off',
          entity_id = 'light.west_lights'
        )
      elif pressed == 2 and not up:
        self.call_service(
          'light/turn_off',
          entity_id = 'light.kitchen_light'
        )
      elif pressed == 3 and not up:
        self.call_service(
          'light/turn_off',
          entity_id = 'light.laundry_room_lights'
        )
      elif pressed == 4 and not up:
        self.log(f'🔕 {switch_name} notification cleared.', ascii_encode=False)
        self.set_color_tracking(notification_tracking_number, self.NOTIF_OFF)
        self.log(f'💼 {switch_name} stored value to 65792 (off).', ascii_encode=False)
        self.set_led_color_now(switch_entity_id, self.NOTIF_OFF)
        self.log(f'🎚 {switch_name} switch changed to 65792 (off).', ascii_encode=False)

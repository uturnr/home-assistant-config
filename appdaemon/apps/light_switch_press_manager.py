import hass_plus

#
# Light Switch Press Manager
#
# Args:
#

class LightSwitchPressManager(hass_plus.HassPlus):
  # Configured for Red Series dimmer
  ZW_LED_PARAM = 16
  ZW_SET_PARAMS_SERVICE = 'zwave_js/bulk_set_partial_config_parameters'
  NOTIF_OFF = 65792
  SWITCHES = [
    {
      'name': 'Bedroom',
      'entity_id': 'light.bedroom_light',
      'node_id': 12,
      'notification_tracking_number': 'input_number.bedroom_notification',
    },
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

      self.log(
        f'🐣 Listening for presses on {switch["name"]} (Node ID {node_id}).'
      )
  
  # def set_color_tracking(self, tracking_number, color):
  #   self.set(tracking_number, color)
  #   # self.call_service(
  #   #   'input_number/set_value',
  #   #   entity_id = tracking_number,
  #   #   value = color
  #   # )
  
  def set_led_color_now(self, entity_id: str, color: int):
    self.call_service(
      self.ZW_SET_PARAMS_SERVICE,
      entity_id = entity_id,
      parameter = self.ZW_LED_PARAM,
      value = color
    )

  def perform_action(
    self,
    switch_name: str,
    pressed: int,
    up: bool,
    notification_tracking_number: int,
    switch_entity_id: str,
  ) -> bool:
    """
    🛌 Bedroom
    """
    if switch_name == 'Bedroom':
      if pressed == 2 and up: # 2️⃣ ⬆️
        self.turn_on('scene.bedroom_bright'); return True
      elif pressed == 3 and up: # 3️⃣ ⬆️
        self.turn_on('light.main_lights'); return True
      elif pressed == 2 and not up: # 2️⃣ ⬇️
        self.turn_on('scene.bedroom_dim'); return True
      elif pressed == 3 and not up: # 3️⃣ ⬇️
        self.turn_off('light.main_lights'); return True

    """
    🍳 Kitchen
    """
    if switch_name == 'Kitchen': # 1️⃣ ⬆️
      if pressed == 1 and up:
        self.turn_on('light.west_lights'); return True
      elif pressed == 2 and up: # 2️⃣ ⬆️
        self.turn_on('light.kitchen_light'); return True
      elif pressed == 3 and up: # 3️⃣ ⬆️
        self.turn_on('light.laundry_room_lights'); return True
      elif pressed == 1 and not up: # 1️⃣ ⬇️
        self.turn_off('light.west_lights'); return True
      elif pressed == 2 and not up: # 2️⃣ ⬇️
        self.turn_off('light.kitchen_light'); return True
      elif pressed == 3 and not up: # 3️⃣ ⬇️
        self.turn_off('light.laundry_room_lights'); return True
      elif pressed == 4 and not up: # 4️⃣ ⬇️
        self.log(f'🔕 {switch_name} notification cleared.')
        self.set(notification_tracking_number, self.NOTIF_OFF)
        self.log(f'💼 {switch_name} stored value to 65792 (off).')
        self.set_led_color_now(switch_entity_id, self.NOTIF_OFF)
        self.log(f'🎚 {switch_name} switch changed to 65792 (off).'); return True

      return False


  def handle_switch_press(self, event_name, data, kwargs):
    switch_name = kwargs['switch_name']
    switch_entity_id = kwargs['switch_entity_id']
    notification_tracking_number = kwargs['notification_tracking_number']

    pressed = None
    # Extract keypress value 1 thru 5 (KeyPressed KeyPressed2x KeyPressed3x ...)
    if data['value'].startswith('KeyPressed'):
      if data['value'].endswith('x'):
        pressed = int(data['value'][10])
      else:
        pressed = 1

    up = None
    if data['label'] == 'Scene 002': # Up
      up = True
    elif data['label'] == 'Scene 001': # Down
      up = False

    if pressed == None or up == None:
      return

    action_performed = self.perform_action(
      switch_name,
      pressed,
      up,
      notification_tracking_number,
      switch_entity_id
    )

    action_log_prefix = '🎚 Last action triggered by'

    if not action_performed:
      # Don’t spam logs for single presses that don’t have actions
      if pressed == 1:
        return
      action_log_prefix = '🤷‍♂️ No action configured for'

    self.log(
      f'{action_log_prefix} pressing {switch_name} {pressed}x {"⬆️" if up else "⬇️"}.'
    )

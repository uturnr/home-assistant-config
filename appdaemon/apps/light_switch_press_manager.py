import hass_plus

#
# Light Switch Press Manager
#
# Args:
#


class LightSwitchPressManager(hass_plus.HassPlus):
  # Configured for Red Series dimmer
  LZW_LED_PARAM = 16
  VZW_LED_PARAM = 99
  ZW_SET_PARAMS_SERVICE = 'zwave_js/bulk_set_partial_config_parameters'
  LZW_NOTIF_OFF = 65792  # Color 0, Brightness 0, Duration 0, Effect Off
  VZW_NOTIF_OFF = 16777473  # Color 0 , Brightness 0, Duration 0, Effect Solid
  VZW_NOTIF_SUCCESS = 124085250  # Green animation 2s small to big
  SWITCHES = [
    {
      'name': 'Bedroom',
      'entity_id': 'light.bedroom_light',
      'model': 'LZW',
      'node_id': 12,
      'notification_tracking_number': 'input_number.bedroom_notification',
    },
    {
      'name': 'Kitchen',
      'entity_id': 'light.kitchen_light',
      'model': 'VZW',
      'node_id': 16,
      'notification_tracking_number': 'input_number.kitchen_notification',
    },
    {
      'name': 'Living Room Fan Switch',
      'entity_id': 'light.red_series_fan_light_switch',
      'model': 'LZW',
      'node_id': 9,
      # TODO: Create input_number.living_room_fan_notification; param may be 24
      'notification_tracking_number': (
        'input_number.living_room_fan_notification'
      ),
    }
  ]

  def initialize(self):
    for switch in self.SWITCHES:
      node_id = switch['node_id']

      # Listen for scenes
      self.listen_event(
        self.handle_switch_press,
        'zwave_js_value_notification',
        node_id=node_id,
        switch_name=switch['name'],
        switch_entity_id=switch['entity_id'],
        switch_model=switch['model'],
        notification_tracking_number=switch['notification_tracking_number']
      )

      self.log(
        f'🐣 Listening for presses on {switch["name"]} (Node ID {node_id}).'
      )

  def parse_scene_press(self, value) -> int | None:
    if not isinstance(value, str):
      return None
    if value == 'KeyPressed':
      return 1
    if not value.startswith('KeyPressed'):
      return None
    if not value.endswith('x'):
      return None
    digits = value[len('KeyPressed'):-1]
    if not digits.isdigit():
      return None
    return int(digits)

  def parse_scene_direction(self, label) -> bool | None:
    if label in ('Scene 002', 'Up Paddle'):
      return True
    if label in ('Scene 001', 'Down Paddle'):
      return False
    return None

  def set_led_color_now(self, entity_id: str, switch_model: str, color: int):
    param = (
      self.LZW_LED_PARAM if switch_model == 'LZW' else self.VZW_LED_PARAM
    )
    self.call_service(
      self.ZW_SET_PARAMS_SERVICE,
      entity_id=entity_id,
      parameter=param,
      value=color
    )

  def perform_action(
    self,
    switch_name: str,
    pressed: int,
    up: bool,
    notification_tracking_number: int,
    switch_entity_id: str,
    switch_model: str
  ) -> bool:
    """
    🛌 Bedroom
    """
    if switch_name == 'Bedroom':
      if pressed == 2 and up:  # 2️⃣ ⬆️
        self.turn_on('scene.bedroom_bright')
        return True
      if pressed == 3 and up:  # 3️⃣ ⬆️
        self.turn_on('light.main_lights')
        return True
      if pressed == 2 and not up:  # 2️⃣ ⬇️
        self.turn_on('scene.bedroom_dim')
        return True
      if pressed == 3 and not up:  # 3️⃣ ⬇️
        self.turn_off('light.main_lights')
        return True

    """
    🍳 Kitchen
    """
    if switch_name == 'Kitchen':
      if pressed == 1 and up:  # 1️⃣ ⬆️
        self.turn_on('light.west_lights')
        return True
      if pressed == 2 and up:  # 2️⃣ ⬆️
        self.turn_on('light.kitchen_light')
        return True
      if pressed == 3 and up:  # 3️⃣ ⬆️
        self.turn_on('light.laundry_room_lights')
        return True
      if pressed == 1 and not up:  # 1️⃣ ⬇️
        self.turn_off('light.west_lights')
        return True
      if pressed == 2 and not up:  # 2️⃣ ⬇️
        self.turn_off('light.kitchen_light')
        return True
      if pressed == 3 and not up:  # 3️⃣ ⬇️
        self.turn_off('light.laundry_room_lights')
        return True
      if pressed == 4 and not up:  # 4️⃣ ⬇️
        if switch_model == 'LZW':
          notif_off = self.LZW_NOTIF_OFF
        else:
          notif_off = self.VZW_NOTIF_SUCCESS
        self.log(f'🔕 {switch_name} notification cleared.')
        self.set(notification_tracking_number, notif_off)
        self.log(f'💼 {switch_name} stored value to {notif_off} (off).')
        self.set_led_color_now(switch_entity_id, switch_model, notif_off)
        self.log(f'🎚 {switch_name} switch changed to {notif_off} (off).')
        return True

    """
    🛋️ Living Room
    """
    if switch_name == 'Living Room Fan Switch':
      if pressed == 2 and up:  # 2️⃣ ⬆️
        self.toggle('light.front_porch_door_glass_custom_fade')
        return True
      if pressed == 3 and up:  # 3️⃣ ⬆️
        if self.get_state('switch.adaptive_lighting_default') == 'off':
          self.turn_on('scene.day_lights')
        else:
          self.turn_on('scene.night_lights')
        return True
      return False

    return False

  def handle_switch_press(self, event_name, data, kwargs):
    switch_model = kwargs['switch_model']
    switch_name = kwargs['switch_name']
    switch_entity_id = kwargs['switch_entity_id']
    notification_tracking_number = kwargs['notification_tracking_number']

    value = data.get('value')
    label = data.get('label')
    pressed = self.parse_scene_press(value)
    up = self.parse_scene_direction(label)

    if pressed is None or up is None:
      self.log(
        f'⏭️ {switch_name} scene ignored: value={value!r} label={label!r}'
      )
      return

    action_performed = self.perform_action(
      switch_name,
      pressed,
      up,
      notification_tracking_number,
      switch_entity_id,
      switch_model
    )

    action_log_prefix = '🎚 Last action triggered by'

    if not action_performed:
      # 1x with no AppDaemon action (living room toggle is an HA automation)
      if pressed == 1:
        direction = '⬆️' if up else '⬇️'
        self.log(
          f'👆 {switch_name} 1x {direction} (no AppDaemon action).'
        )
        return
      action_log_prefix = '🤷‍♂️ No action configured for'

    direction = '⬆️' if up else '⬇️'
    self.log(
      f'{action_log_prefix} pressing {switch_name} {pressed}x {direction}.'
    )

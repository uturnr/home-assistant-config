import hass_plus


class LightSwitchNotificationManager(hass_plus.HassPlus):
  LZW_LED_PARAM = 16
  VZW_LED_PARAM = 99
  ZW_SET_PARAM = 'zwave_js/bulk_set_partial_config_parameters'
  # https://inovelliusa.github.io/inovelli-switch-toolbox/
  LZW_NOTIF_OFF = 65792 # Color 0, Brightness 0, Duration 0, Effect Off
  VSW_NOTIF_OFF = 16777473 # Color 0 , Brightness 0, Duration 0, Effect Solid
  VZW_NOTIF_SUCCESS = 124085250 # Green animation 2s small to big
  LZW_COLORS = {
    'compost_green': 33489975, # Color 55, Bright 4, Infinity, Effect Solid
    'garbage_brown': 33489170, # Color 18, Bright 1, Infinity, Effect Solid
    'recycling_blue': 33490080, # Color 160, Bright 4, Infinity, Effect Solid
    'off': 65792 # Color 0, Brightness 0, Duration 0, Effect Off
  }
  VZW_COLORS = {
    'compost_green': 20392191, # Color 55, Bright 40, Infinity, Effect Solid
    'garbage_brown': 17696511, # Color 14, Bright 6, Infinity, Effect Solid
    'recycling_blue': 27273471, # Color 160, Bright 40, Infinity, Effect Solid
    'off': 16777473 # Color 0 , Brightness 0, Duration 0, Effect Solid
  }
  SWITCHES = [
    {
      'name': 'Bedroom',
      'entity_id': 'light.bedroom_light',
      'model': 'LZW',
      'node_id': 12,
      'notify_when_off': False,
      'tracking_number': 'input_number.bedroom_notification',
      'notifications': []
    },
    {
      'name': 'Kitchen',
      'entity_id': 'light.kitchen_light',
      'model': 'VZW',
      'node_id': 16,
      'notify_when_off': True,
      'tracking_number': 'input_number.kitchen_notification',
      'notifications': [
        {
          'name': 'Garbage',
          'entity_id': 'binary_sensor.garbage_day_notification',
          'color': 'garbage_brown'
        },
        {
          'name': 'Recycling',
          'entity_id': 'binary_sensor.recycling_day_notification',
          'color': 'recycling_blue'
        },
        {
          'name': 'Compost',
          'entity_id': 'binary_sensor.compost_day_notification',
          'color': 'compost_green'
        }
      ]
    }
  ]

  def initialize(self):
    # Uncomment to test notification colors.
    # self.set_led_color_now('light.kitchen_light', 'VZW', 17696511)
    for switch in self.SWITCHES:
      notify_when_off = switch['notify_when_off']
      # Track switch toggles for on-only, persisent notifications. (Off when
      # lights off, on when lights on.) Note: The Inovelli Red dimmer seems to
      # persist notifications, the functionality is only needed to ensure
      # that notifications do not show when the switch is off.
    #   if notify_when_off == False:
    #     self.listen_state(
    #       self.handle_switch_toggled,
    #       switch['entity_id'],
    #       tracking_number = switch['tracking_number']
    #     )
    #     self.log(f"🐣 Listening for changes to the {switch['name']} switch.")

      # Listening for notification clearing takes place in light_switch_press_manager
      # TODO: remove duplication of code between these apps.

      for notification in switch['notifications']:
        # Immediately set, then listen to variables to set notification colors.
        self.listen_state(
          self.handle_notification_variable_toggled,
          notification['entity_id'],
          switch_entity_id = switch['entity_id'],
          switch_model = switch['model'],
          tracking_number = switch['tracking_number'],
          notification_name = notification['name'],
          color = notification['color'],
          notify_when_off = notify_when_off,
          immediate = True,
        )
        self.log(f"🐣 Listening for changes to the {notification['name']} notification.")

#   def handle_switch_toggled(self, entity_id, attribute, old, new, kwargs):
#     # Persist notifications by toggling the notifications on when the light
#     # is turned on, and off when the light is turned off.
#     entity_state = self.get_state(entity_id, attribute='all')
#     name = entity_state['attributes']['friendly_name']
#     tracking_number = kwargs['tracking_number']
#     current_tracked_number = int(float(self.get_state(tracking_number)))

#     if new == 'on':
#       new_color = current_tracked_number
#     else:
#       new_color = self.NOTIF_OFF

#     color_id = self.set_led_color_now(entity_id, new_color)
#     self.log(f"🎚 {name} {new}. Set to {new_color}.")

  def handle_notification_variable_toggled(self, entity, attribute, old, new, kwargs):
    # When a variable is changed, set the tracking entity to the appropriate
    # notification color.
    switch_entity_id = kwargs['switch_entity_id']
    switch_model = kwargs['switch_model']
    tracking_number = kwargs['tracking_number']
    notification_name = kwargs['notification_name']
    color = kwargs['color']
    notify_when_off = kwargs['notify_when_off']

    entity_state = self.get_state(switch_entity_id, attribute='all')
    switch_name = entity_state['attributes']['friendly_name']
    switch_state = entity_state['state']

    if new == 'on':
      colors = self.LZW_COLORS if switch_model == 'LZW' else self.VZW_COLORS
      color_id = colors[color]
      # If switch is on when variable toggle, activate the notification.
      if switch_state == 'on' or notify_when_off:
        self.set_led_color_now(switch_entity_id, switch_model, color_id)
        self.log(f"🌈 {switch_name} color {color} ({color_id}) immediately triggered.")

        self.set(tracking_number, color_id)
        self.log(f"💼 {notification_name} to {new}. Color variable set to {color_id} ({color}).")
    else:
      self.log(f"💼 {notification_name} to {new}. Color variable unchanged.")

  def set_led_color_now(self, entity_id: str, switch_model: str, color_id: str):
    param = self.LZW_LED_PARAM if switch_model == 'LZW' else self.VZW_LED_PARAM

    self.call_service(
      self.ZW_SET_PARAM,
      entity_id = entity_id,
      parameter = param,
      value = color_id
    )

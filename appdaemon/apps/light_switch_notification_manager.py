import hass_plus

#
# Light Switch Notification Manager
#
# Args:
#

class LightSwitchNotificationManager(hass_plus.HassPlus):
  ZW_PARAM = 16
  ZW_SET_PARAM = 'zwave_js/bulk_set_partial_config_parameters'
  NOTIF_OFF = 65792
  COLORS = {
    'garbage_green': 33490016,
    'recycling_blue': 33490080,
  }
  SWITCHES = [
    {
      'name': 'Bedroom',
      'entity_id': 'light.bedroom_light',
      'node_id': 12,
      'notify_when_off': False,
      'tracking_number': 'input_number.bedroom_notification',
      'notifications': []
    },
    {
      'name': 'Kitchen',
      'entity_id': 'light.kitchen_light',
      'node_id': 8,
      'notify_when_off': True,
      'tracking_number': 'input_number.kitchen_notification',
      'notifications': [
        {
          'name': 'Garbage',
          'entity_id': 'variable.garbage_day_notification',
          'color': 'garbage_green'
        },
        {
          'name': 'Recycling',
          'entity_id': 'variable.recycling_day_notification',
          'color': 'recycling_blue'
        }
      ]
    }
  ]

  def initialize(self):
    for switch in self.SWITCHES:
      notify_when_off = switch['notify_when_off']
      # Track switch toggles for on-only, persisent notifications. (Off when
      # lights off, on when lights on.) Note: The Inovelli Red dimmer seems to
      # persist notifications, the functionality is only needed to ensure
      # that notifications do not show when the switch is off.
      if notify_when_off == False:
        self.listen_state(
          self.handle_switch_toggled,
          switch['entity_id'],
          tracking_number = switch['tracking_number']
        )
        self.log(f"🐣 Listening for changes to the {switch['name']} switch.")

      # Listening for notification clearing takes place in light_switch_press_manager
      # TODO: remove duplication of code between these apps.

      for notification in switch['notifications']:
        # Immediately set, then listen to variables to set notification colors.
        self.listen_state(
          self.handle_notification_variable_toggled,
          notification['entity_id'],
          switch_entity_id = switch['entity_id'],
          tracking_number = switch['tracking_number'],
          notification_name = notification['name'],
          color = notification['color'],
          notify_when_off = notify_when_off,
          immediate = True,
        )
        self.log(f"🐣 Listening for changes to the {notification['name']} notification.")

  def handle_switch_toggled(self, entity_id, attribute, old, new, kwargs):
    # Persist notifications by toggling the notifications on when the light
    # is turned on, and off when the light is turned off.
    entity_state = self.get_state(entity_id, attribute='all')
    name = entity_state['attributes']['friendly_name']
    tracking_number = kwargs['tracking_number']
    current_tracked_number = int(float(self.get_state(tracking_number)))

    if new == 'on':
      new_color = current_tracked_number
    else:
      new_color = self.NOTIF_OFF

    self.set_led_color_now(entity_id, new_color)
    self.log(f"🎚 {name} {new}. Set to {new_color}.")

  def handle_notification_variable_toggled(self, entity, attribute, old, new, kwargs):
    # When a variable is changed, set the tracking entity to the appropriate
    # notification color.
    switch_entity_id = kwargs['switch_entity_id']
    tracking_number = kwargs['tracking_number']
    notification_name = kwargs['notification_name']
    color = kwargs['color']
    notify_when_off = kwargs['notify_when_off']

    entity_state = self.get_state(switch_entity_id, attribute='all')
    switch_name = entity_state['attributes']['friendly_name']
    switch_state = entity_state['state']

    if new == 'True':
      new_color_name = color
      new_color = self.COLORS[color]
    else:
      new_color_name = 'off'
      new_color = self.NOTIF_OFF

    # If switch is on when variable toggle, activate the notification.
    if switch_state == 'on' or notify_when_off:
      self.set_led_color_now(switch_entity_id, new_color)
      self.log(f"🌈 {switch_name} color {new_color_name} ({new_color}) immediately triggered.")

    self.set(tracking_number, new_color)
    self.log(f"💼 {notification_name} to {new}. Color variable set to {new_color_name} ({new_color}).")

  def set_led_color_now(self, entity_id, color):
    self.call_service(
      self.ZW_SET_PARAM,
      entity_id = entity_id,
      parameter = self.ZW_PARAM,
      value = color
    )

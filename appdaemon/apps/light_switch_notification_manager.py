import appdaemon.plugins.hass.hassapi as hass

#
# Light Switch Notification Manager
#
# Args:
#

class LightSwitchNotificationManager(hass.Hass):
  ZW_PARAM = 16
  ZW_NOTIF_COLOR = 'ozw/set_config_parameter'
  NOTIF_TRACK_COLOR = 'input_number/set_value'
  SWITCHES = [
    {
      'name': 'Bedroom',
      'entity': 'light.bedroom_light',
      'notify_when_off': False,
      'tracking_number': 'input_number.bedroom_notification',
      'notifications': []
    },
    {
      'name': 'Kitchen',
      'entity': 'light.kitchen_light',
      'notify_when_off': True,
      'tracking_number': 'input_number.kitchen_notification',
      'notifications': [
        {
          'name': 'Garbage',
          'entity': 'variable.garbage_day_notification',
          'color': 33490016
        },
        {
          'name': 'Recycling',
          'entity': 'variable.recycling_day_notification',
          'color': 33490080
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
          switch['entity'],
          tracking_number = switch['tracking_number']
        )
        self.log(f"Listening for changes to the {switch['name']} switch.")
      # Listen for notifications being cleared (4 taps down)
      entity_state = self.get_state(switch['entity'], attribute='all')
      node_id = entity_state['attributes']['node_id']

      self.listen_event(
        self.handle_notification_cleared,
        'ozw.scene_activated',
        node_id = node_id,
        scene_id = 1,
        scene_value_label = 'Pressed 4 Times',
        switch_entity = switch['entity'],
        tracking_number = switch['tracking_number'],
      )
      self.log(f"Listening for {switch['name']} switch 4x down.")
      for notification in switch['notifications']:
        # Listen to variables to set notification colors.
        self.listen_state(
          self.handle_notification_variable_toggled,
          notification['entity'],
          switch_entity = switch['entity'],
          tracking_number = switch['tracking_number'],
          name = notification['name'],
          color = notification['color'],
          notify_when_off = notify_when_off,
        )
        self.log(f"Listening for changes to the {notification['name']} notification.")

  def handle_switch_toggled(self, entity, attribute, old, new, kwargs):
    # Persist notifications by toggling the notifications on when the light
    # is turned on, and off when the light is turned off.
    entity_state = self.get_state(entity, attribute='all')
    node_id = entity_state['attributes']['node_id']
    name = entity_state['attributes']['friendly_name']
    tracking_number = kwargs['tracking_number']
    current_tracked_number = int(float(self.get_state(tracking_number)))

    if new == 'on':
      new_color = current_tracked_number
    else:
      new_color = 0

    self.set_led_color_now(node_id, new_color)
    self.log(f"{name} {new}. Set to {new_color}.")

  def handle_notification_variable_toggled(self, entity, attribute, old, new, kwargs):
    # When a variable is changed, set the tracking entity to the appropriate
    # notification color.
    switch_entity = kwargs['switch_entity']
    tracking_number = kwargs['tracking_number']
    name = kwargs['name']
    color = kwargs['color']
    notify_when_off = kwargs['notify_when_off']

    entity_state = self.get_state(switch_entity, attribute='all')
    node_id = entity_state['attributes']['node_id']
    switch_name = entity_state['attributes']['friendly_name']
    switch_state = entity_state['state']

    if new == 'True':
      new_color = color
    else:
      new_color = 0

    # If switch is on when variable toggle, activate the notification.
    if switch_state == 'on' or notify_when_off:
      self.set_led_color_now(node_id, new_color)
      self.log(f"{switch_name} color {new_color} immediately triggered.")

    self.set_color_tracking(tracking_number, new_color)
    self.log(f"{name} to {new}. Color variable set to {new_color}.")

  def handle_notification_cleared(self, event_name, data, kwargs):
    switch_entity = kwargs['switch_entity']
    tracking_number = kwargs['tracking_number']
    entity_state = self.get_state(switch_entity, attribute='all')
    node_id = entity_state['attributes']['node_id']
    switch_name = entity_state['attributes']['friendly_name']

    self.log(f"{switch_name} notification cleared.")
    self.set_color_tracking(tracking_number, 0)
    self.log('Stored value to 0.')
    self.set_led_color_now(node_id, 0)
    self.log('Switch changed to 0.')

  def set_led_color_now(self, node_id, color):
    self.call_service(
      self.ZW_NOTIF_COLOR,
      node_id = node_id,
      parameter = self.ZW_PARAM,
      value = color
    )

  def set_color_tracking(self, tracking_number, color):
    self.call_service(
      self.NOTIF_TRACK_COLOR,
      entity_id = tracking_number,
      value = color
    )
    

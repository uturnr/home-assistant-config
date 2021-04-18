import appdaemon.plugins.hass.hassapi as hass

#
# Light Switch Press Manager
#
# Args:
#

class LightSwitchPressManager(hass.Hass):
  # Configured for Red Series dimmer
  SWITCHES = [
    {
      'name': 'Kitchen',
      'entity': 'light.kitchen_light',
    }
  ]

  def initialize(self):
    for switch in self.SWITCHES:
      # Track switch toggles for on-only, persisent notifications. (Off when
      # lights off, on when lights on.) Note: The Inovelli Red dimmer seems to
      # persist notifications, the functionality is only needed to ensure
      # that notifications do not show when the switch is off.
      switch_state = self.get_state(switch['entity'], attribute = 'all')
      node_id = switch_state['attributes']['node_id']

      # Listen for scenes
      self.listen_event(
        self.handle_switch_press,
        'ozw.scene_activated',
        node_id = node_id,
        switch_name = switch['name'],
        switch_entity = switch['entity'],
      )

  def handle_switch_press(self, event_name, data, kwargs):
    # Persist notifications by toggling the notifications on when the light
    # is turned on, and off when the light is turned off.

    # switch_entity = kwargs['switch_entity']
    name = kwargs['switch_name']

    pressed = None
    if data['scene_value_id'] == 1: # Pressed 1 time
      pressed = 1
    elif data['scene_value_id'] == 4: # Pressed 2 times
      pressed = 2
    elif data['scene_value_id'] == 5: # Pressed 3 times
      pressed = 3

    up = None
    if data['scene_id'] == 2: # Up
      up = True
    elif data['scene_id'] == 1: # Down
      up = False

    if name == 'Kitchen':
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

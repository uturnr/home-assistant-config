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

      self.log(f'🐣 Listening for presses on {switch["name"]} (Node ID {node_id}).', ascii_encode=False)

  def handle_switch_press(self, event_name, data, kwargs):
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

    if pressed == None or up == None:
      return

    self.log(f'{name} switch pressed {pressed}x {"up" if up else "down"}.')

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

from array import array
import appdaemon.plugins.hass.hassapi as hass
from typing import Union

#
# Extend hass.Hass with helpers
#

class HassPlus(hass.Hass):

  def initialize(self):
    self.log('🐣 Initializing Hass Plus!')

  """
  Log with emojis
  """
  def log(self, message):
    hass.Hass.log(self, message, ascii_encode=False)

  """
  Notify and log
  """
  def notify(self, title: str, message: str):
    self.log(f'💌 Notification sent: {title}: {message}')
    self.call_service(
      'notify/mobile_app_cphone',
      title = title,
      message = message,
    )

  """
  Update value of:
   - input_number
   - input_boolean
   - variable
  """
  def set(self, entity_id: str, value: Union[str, int, bool]):
    # variable.set_variable -> variable
    entity_type = entity_id.split('.')[0]
    # variable.set_variable -> set_variable
    entity_name = entity_id.split('.')[1]

    def generic_set(service: str):
      self.call_service(
        service,
        entity_id = entity_id,
        value = value,
      )

    def set_input_boolean():
      self.call_service(
        f'input_boolean/turn_{value}',
        entity_id = entity_id,
      )
    def set_input_number():
      generic_set('input_number/set_value')
    def set_variable():
      self.call_service(
        'variable/set_variable',
        variable = entity_name,
        value = value,
      )



    setters = {
      'input_number': set_input_number,
      'input_boolean': set_input_boolean,
      'variable': set_variable,
    }

    setters[entity_type]()

    self.log(f'⚙️ {entity_id} to {value}')

  """
  On/off light, switch, scene helper
  """
  def turn(self, on: bool, entity_id: str):
    value = 'on' if on else 'off'
    service_type = entity_id.split('.')[0]
    if service_type == 'scene':
      assert on, 'turn_off not supported for scenes'
    self.call_service(
      f'{service_type}/turn_{value}',
      entity_id = entity_id,
    )
    self.log(f'⚙️ {entity_id} to {value}')
  
  """
  Turn on light, switch or scene
  """
  def turn_on(self, entity_id: str):
    self.turn(True, entity_id)
  
  """
  Turn off light, switch
  """
  def turn_off(self, entity_id: str):
    self.turn(False, entity_id)

  """
  Adjust brightness/color for lights that are already on within a light group
  """
  def adjust_lights(
    self,
    entity_id: str,
    brightness: Union[int, None],
    color_temp: Union[int, None],
  ):
    if not self.get_state(entity_id) == 'on':
      return
    # Entities that need to be checked whether they are light or group, mark
    # true once processed.
    light_queue: dict[str, bool] = { entity_id: False }
    # Entities that are confirmed light and are on
    lights_to_adjust: list[str] = []

    # Gather all child lights
    all_lights_processed = False
    while not all_lights_processed:
      lights_not_processed = 0
      lights_to_add_to_queue: list[str] = []

      for light_item in light_queue.items():
        light = light_item[0]
        light_already_processed = light_item[1]

        # Mark current light/light group as processed
        light_queue[light] = True
        
        if light_already_processed:
          continue
        else:
          lights_not_processed += 1
        child_lights: Union[list[str], str] = self.get_state(
          light,
          'entity_id',
        )
        if (
          isinstance(child_lights, str)
          and self.get_state(light) == 'on'
        ):
          # If entity_id is returned as string, this is a light
          lights_to_adjust.append(light)
        elif (
          isinstance(child_lights, list)
        ):
          # If entity_id is an array, this is a light group.
          lights_to_add_to_queue += child_lights

      for new_light in lights_to_add_to_queue:
        light_queue[new_light] = False

      if lights_not_processed == 0:
        all_lights_processed = True

    lights_adjusted_str = ', '.join(lights_to_adjust)

    # TODO: make simultaneous
    for light in lights_to_adjust:
      kwargs = {
        "brightness": brightness,
        "color_temp": color_temp,
      }
      self.call_service(
        'light/turn_on',
        entity_id = light,
        **{k: v for k, v in kwargs.items() if v is not None}
      )

    lights_adjusted_str = ', '.join(lights_to_adjust)
    self.log(f'⚙️ {entity_id} adjusted ({lights_adjusted_str})')

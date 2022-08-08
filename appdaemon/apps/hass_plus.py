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
  def log(self, message: str):
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

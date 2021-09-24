import appdaemon.plugins.hass.hassapi as hass
from datetime import datetime, timedelta

#
# App to localize frequently used functions
#

class Utils(hass.Hass):

  def initialize(self):
    self.log(f'🐣 Initializing utilities!', ascii_encode=False)

  def set_input(self, entity_id, value):
    """
    Update value of input_number or input_boolean
    """
    entity_type = entity_id.split('.')[0]
    if entity_type == 'input_boolean':
      self.call_service(
        f'input_boolean/turn_{value}',
        entity_id = entity_id,
      )
    elif entity_type == 'input_number':
      self.call_service(
        f'input_number/set_value',
        entity_id = entity_id,
        value = value,
      )
    self.log(f'⚙️ {entity_id} to {value}', ascii_encode=False)

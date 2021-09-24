import appdaemon.plugins.hass.hassapi as hass
import datetime
import requests
import secrets

#
# Get Waste Schedule
#
# Args:
#

class GetWasteSchedule(hass.Hass):
  def initialize(self):
    self.run_in(self.reset, 0)
    self.fetch_schedules()
    self.run_daily(self.reset, '04:25:00')
    self.run_daily(self.daily_fetch_schedules, '04:30:00')

  def daily_fetch_schedules(self, kwargs):
    self.fetch_schedules()
  
  def fetch_schedules(self):
    # WASTE_TYPES contains a list of maps like:
    # {
    #   'name': 'garbage',
    #   'url': <API url for garbage schedule>
    # }
    for type in secrets.WASTE_TYPES:
      earliest_day = None
      name = type['name']
  
      for url in type['url']:
        r = requests.get(url)
        data = r.json()

        for event in data['events']:
          if event['flags'][0]['name'] == name:
            if earliest_day is None or event['day'] < earliest_day:
              earliest_day = event['day']
            break
      
      if earliest_day is not None:
        self.update_notifications(name, earliest_day)

  def update_notifications(self, name, nextDate):
    notification_name = f'{name}_day_notification'
    
    # Set notification variable to true if tomorrow is pickup day.
    tomorrow_date_obj = datetime.date.today() + datetime.timedelta(days=1)
    date_obj = datetime.datetime.strptime(nextDate, '%Y-%m-%d').date()
    tomorrow_is_day = tomorrow_date_obj == date_obj
    if tomorrow_is_day:
      self.log(f'{name.capitalize()} day is tomorrow.')
      self.call_service(
        'variable/set_variable',
        variable=notification_name,
        value=tomorrow_is_day
      )
    else:
      self.log(f'Next {name} day is {nextDate}')

  def reset(self, kwargs):
    self.log('♻️ Resetting waste variables to False.', ascii_encode=False)
    for type in secrets.WASTE_TYPES:
      name = type['name']
      notification_name = f'{name}_day_notification'
      self.call_service(
        'variable/set_variable',
        variable=notification_name,
        value=False
      )

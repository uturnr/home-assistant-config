import hass_plus
import datetime
import requests
import secrets

#
# Get Waste Schedule
#
# Args:
#

class GetWasteSchedule(hass_plus.HassPlus):
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
    #   'url': [<API url(s) for garbage schedule>],
    #   'emoji': '🗑',
    # }
    for type in secrets.WASTE_TYPES:
      earliest_day = None
      name = type['name']
      emoji = type['emoji']
  
      for url in type['url']:
        r = requests.get(url)
        data = r.json()

        for event in data['events']:
          if event['flags'][0]['name'] == name:
            if earliest_day is None or event['day'] < earliest_day:
              earliest_day = event['day']
            break
      
      if earliest_day is not None:
        self.update_notifications(name, earliest_day, emoji)

  def update_notifications(self, name: str, nextDate: str, emoji: str):
    notification_variable = f'variable.{name}_day_notification'
    
    # Set notification variable to true if tomorrow is pickup day.
    tomorrow_date_obj = datetime.date.today() + datetime.timedelta(days=1)
    date_obj = datetime.datetime.strptime(nextDate, '%Y-%m-%d').date()
    tomorrow_is_day = tomorrow_date_obj == date_obj
    if tomorrow_is_day:
      self.log(f'{emoji} {name.capitalize()} day is tomorrow.')
      self.set(notification_variable, tomorrow_is_day)
    else:
      self.log(f'{emoji} Next {name} day is {nextDate}')

  def reset(self, kwargs):
    self.log('🚮 Resetting waste variables to False.')
    for type in secrets.WASTE_TYPES:
      name = type['name']
      notification_variable = f'variable.{name}_day_notification'
      self.set(notification_variable, False)

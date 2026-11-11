import hass_plus
import datetime
import requests
import my_secrets


class GetWasteSchedule(hass_plus.HassPlus):
  def initialize(self):
    self.reset()
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
    for type in my_secrets.WASTE_TYPES:
      self.log(type)
      earliest_day = None
      name = type['name']
      api_name = type['api_name']
      emoji = type['emoji']

      for url in type['url']:
        r = requests.get(url)
        # Check if the request was successful.
        if r.status_code != 200:
          self.log(f'🚨 Error fetching {name} schedule: {r.status_code}')
          continue
        data = r.json()

        self.log(data['events'])

        for event in data['events']:
          if event['flags'][0]['name'] == api_name:
            if earliest_day is None or event['day'] < earliest_day:
              earliest_day = event['day']
            break

      if earliest_day is not None:
        self.update_notifications(name, earliest_day, emoji)

  def update_notifications(self, name: str, nextDate: str, emoji: str):
    notification_variable = f'binary_sensor.{name}_day_notification'

    # Set notification variable to true if tomorrow is pickup day.
    tomorrow_date_obj = datetime.date.today() + datetime.timedelta(days=1)
    date_obj = datetime.datetime.strptime(nextDate, '%Y-%m-%d').date()
    tomorrow_is_day = tomorrow_date_obj == date_obj
    if tomorrow_is_day:
      self.log(f'{emoji} {name.capitalize()} day is tomorrow.')
      self.set(notification_variable, 'true')
    else:
      self.log(f'{emoji} Next {name} day is {nextDate}')

  def reset(self):
    self.log('🚮 Resetting waste variables to False.')
    for type in my_secrets.WASTE_TYPES:
      name = type['name']
      notification_variable = f'binary_sensor.{name}_day_notification'
      self.set(notification_variable, 'false')

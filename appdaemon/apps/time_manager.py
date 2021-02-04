import appdaemon.plugins.hass.hassapi as hass
import datetime

#
# Time Manager
#
# Args:
#

class TimeManager(hass.Hass):
  def initialize(self):
    time = datetime.time(0, 0, 0)
    self.run_minutely(
      self.handle_minute_changed,
      time
    )
    self.handle_minute_changed(time)

  def handle_minute_changed(self, time):
    now = self.datetime().now()
    current_time_str = now.strftime("%H:%M:00")

    self.WakeupService = self.get_app("wakeup_service")
    self.WakeupService.handle_minute_changed(current_time_str)

    self.TurndownService = self.get_app("turndown_service")
    self.TurndownService.handle_minute_changed(current_time_str)


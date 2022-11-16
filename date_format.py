import datetime
from datetime import date

months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November",
          "December"]


class DateFormatted:
    def __init__(self, date: date = datetime.datetime.now().date()):
        self.year = date.year
        self.month = months[date.month - 1]
        self.day = date.day

    def format_it(self):
        return self.month + " " + str(self.day) + " " + str(self.year)

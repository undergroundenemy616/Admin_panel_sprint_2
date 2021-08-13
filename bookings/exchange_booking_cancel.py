import os
from datetime import datetime
import pytz
from exchangelib import Credentials, Configuration, DELEGATE, Account as Ac


def exchange_booking_cancel(instance):
    if instance.bookings.all()[0].table.room.exchange_email:
        credentials = Credentials(os.environ['EXCHANGE_ADMIN_LOGIN'], os.environ['EXCHANGE_ADMIN_PASS'])
        config = Configuration(server=os.environ['EXCHANGE_SERVER'], credentials=credentials)
        account_exchange = Ac(primary_smtp_address=os.environ['EXCHANGE_ADMIN_LOGIN'], config=config,
                              autodiscover=False, access_type=DELEGATE)
        date_from = instance.bookings.all()[0].date_from
        date_to = instance.bookings.all()[0].date_to
        start = datetime(date_from.year, date_from.month,
                         date_from.day, date_from.hour,
                         date_from.minute, tzinfo=pytz.UTC)
        end = datetime(date_to.year, date_to.month,
                       date_to.day, date_to.hour,
                       date_to.minute, tzinfo=pytz.UTC)
        for calendar_item in account_exchange.calendar.filter(start=start, end=end):
            if calendar_item.organizer.email_address == account_exchange.primary_smtp_address and \
                    instance.bookings.all()[0].table.room.exchange_email == calendar_item.location:
                calendar_item.cancel()

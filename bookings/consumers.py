import json
import datetime
import logging

import pytz
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.db.models import Q

from bookings.models import Booking
import bookings.models
import asyncio
from functools import wraps, partial
from rooms.models import Room


def async_wrap(func):
    @wraps(func)
    async def run(*args, loop=None, executor=None, **kwargs):
        if loop is None:
            loop = asyncio.get_event_loop()
        pfunc = partial(func, *args, **kwargs)
        return await loop.run_in_executor(executor, pfunc)

    return run


class BookingConsumer(AsyncJsonWebsocketConsumer):

    def __init__(self, *args, **kwargs):
        self.logger = logging.getLogger('bookings')
        super().__init__(*args, **kwargs)

    async def connect(self):

        # Join group TODO: Make only auth connection
        # await self.channel_layer.group_add(
        #     "dimming",
        #     self.channel_name
        # )
        await self.accept()
        self.logger.warning(msg='Web socket connected')

    async def receive_json(self, content, **kwargs):
        self.logger.warning(msg='try to find right method')
        res = dict()
        if content.get('event', None) == 'echo':
            res = content
        else:
            bookings.models.GLOBAL_TABLES_CHANNEL_NAMES[f'{content.get("table")}'] = self.channel_name
            if not bookings.models.GLOBAL_DATETIME_FROM_WS.get(f'{content.get("table")}'):
                utc = pytz.UTC
                bookings.models.GLOBAL_DATE_FROM_WS[f'{content.get("table")}'] = datetime.datetime.now().date()
                bookings.models.GLOBAL_DATETIME_FROM_WS[f'{content.get("table")}'] = datetime.datetime.now().replace(tzinfo=utc)
                bookings.models.GLOBAL_DATETIME_TO_WS[f'{content.get("table")}'] = datetime.datetime.utcnow().replace(tzinfo=utc) + datetime.timedelta(hours=1)
            if content.get('event', None) == 'daily_booking':
                content = await self.check_db_for_day_booking(date=content.get('date', str(datetime.date.today())),
                                                              table=content.get('table', None))

                res = {
                    'type': 'send_json',
                    'text': {
                        'type': 'timeline',
                        'data': content
                    }
                }
            elif content.get('event', None) == 'hours_booking':
                if not bookings.models.GLOBAL_DATETIME_FROM_WS.get(f'{content.get("table")}'):
                    utc = pytz.UTC
                    bookings.models.GLOBAL_DATE_FROM_WS[f'{content.get("table")}'] = datetime.datetime.now().date()
                    bookings.models.GLOBAL_DATETIME_FROM_WS[
                        f'{content.get("table")}'] = datetime.datetime.now().replace(tzinfo=utc)
                    bookings.models.GLOBAL_DATETIME_TO_WS[
                        f'{content.get("table")}'] = datetime.datetime.utcnow().replace(
                        tzinfo=utc) + datetime.timedelta(hours=1)
                bookings.models.GLOBAL_TABLES_CHANNEL_NAMES[f'{content.get("table")}'] = self.channel_name
                content = await self.check_db_for_datetime_booking(date_from_str=content.get('date_from', str(datetime.date.today())),
                                                                   date_to_str=content.get('date_to', None),
                                                                   table=content.get('table', None))

                res = {
                    'type': 'send_json',
                    'text': {
                        'type': 'meeting_block',
                        'data': content
                    }
                }
        await self.channel_layer.send(f'{self.channel_name}', res)

    @classmethod
    async def decode_json(cls, text_data):
        try:
            return json.loads(text_data)
        except Exception as e:
            res = {
                'event': 'echo',
                'type': 'send_message',
                'text': text_data
            }
            return res

    async def send_json(self, content, close=False):
        """
        Encode the given content as JSON and send it to the client.
        """
        self.logger.warning(msg='try send json to all')
        if content.get('text'):
            await super().send(text_data=await self.encode_json(content['text']), close=close)
        else:
            await super().send(text_data=await self.encode_json(content), close=close)

    async def send_message(self, res=None):
        """ Receive message from room group """
        # Send message to WebSocket
        if res['event'] == 'new_booking':
            await self.send_json({
                "new_booking": res['message'],
            })
        elif res['event'] == 'canceled_booking':
            await self.send_json({
                "canceled_booking": res['message'],
            })
        elif res['event'] == 'over_booking':
            await self.send_json({
                "over_booking": res['message'],
            })
        elif res['event'] == 'echo':
            await self.send_json({
                "echo": "pong",
            })
        self.logger.warning(msg='sending response')

    async def disconnect(self, close_code):
        # Delete connection from group
        await self.channel_layer.group_discard(
            "dimming",
            self.channel_name
        )
        self.logger.warning(msg="Web socket disconnected")

    @staticmethod
    @async_wrap
    def check_db_for_day_booking(date=None, table=None):
        if not date:
            date = []
        date_from_str = datetime.datetime.strptime(date, '%Y-%m-%d').date()
        bookings.models.GLOBAL_DATE_FROM_WS[f'{table}'] = date_from_str
        existing_booking = Booking.objects.filter(table=table,
                                                  status__in=['waiting', 'active'],
                                                  date_from__year=str(date_from_str.year),
                                                  date_from__month=str(date_from_str.month),
                                                  date_from__day=str(date_from_str.day))
        result = []
        local_tz = pytz.timezone('Europe/Moscow')
        for booking in existing_booking:
            result.append({
                'id': str(booking.id),
                'date_from': str(booking.date_from.astimezone(local_tz))[0:16],
                'date_to': str(booking.date_to.astimezone(local_tz))[0:16]
            })
        return result

    @staticmethod
    @async_wrap
    def check_db_for_datetime_booking(date_from_str=None, date_to_str=None, table=None):
        logger = logging.getLogger('bookings')
        if not date_from_str:
            period = []
        logger.warning(msg='Check_hourly_booking')
        local_tz = pytz.timezone('Europe/Moscow')
        date_from = datetime.datetime.strptime(date_from_str, '%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=datetime.timezone.utc)
        date_to = datetime.datetime.strptime(date_to_str, '%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=datetime.timezone.utc)
        bookings.models.GLOBAL_DATETIME_FROM_WS[f'{table}'] = date_from
        bookings.models.GLOBAL_DATETIME_TO_WS[f'{table}'] = date_to
        overflows = Booking.objects.filter(table=table, is_over=False, status__in=['waiting', 'active']). \
            filter((Q(date_from__lt=date_to, date_to__gte=date_to)
                    | Q(date_from__lte=date_from, date_to__gt=date_from)
                    | Q(date_from__gte=date_from, date_to__lte=date_to)) & Q(date_from__lt=date_to))
        if overflows:
            result = []
            for booking in overflows:
                result.append({
                    'status': 'occupied',
                    'id': str(booking.id),
                    'title': str(booking.table.room.title),
                    'date_from': str(booking.date_from.astimezone(local_tz))[:16],
                    'date_to': str(booking.date_to.astimezone(local_tz))[:16],
                    'user': {
                        'id': str(booking.user.id),
                        'phone': str(booking.user.user.phone_number),
                        'firstname': str(booking.user.first_name),
                        'lastname': str(booking.user.last_name),
                        'middlename': str(booking.user.middle_name),
                    },
                    'theme': str(booking.theme)
                })
            return result
        empty_result = []
        rooms = Room.objects.filter(tables__in=[table, ])
        for room in rooms:
            table = room.tables.first()
            images = room.images.first()
            if images:
                empty_result = {
                    'id': str(room.id),
                    'title': str(room.title),
                    'tables': [
                        {'id': str(table.id),
                         'title': str(table.title),
                         'is_occupied': str(False)}
                    ],
                    'images': [{
                        'id': str(images.id),
                        'title': str(images.title),
                        'path': str(images.path),
                        'thumb': str(images.thumb)
                    }],
                    'status': 'not occupied'
                }
            else:
                empty_result = {
                    'id': str(room.id),
                    'title': str(room.title),
                    'tables': [
                        {'id': str(table.id),
                         'title': str(table.title),
                         'is_occupied': str(False)}
                    ],
                    'images': [],
                    'status': 'not occupied'
                }
        return [empty_result]

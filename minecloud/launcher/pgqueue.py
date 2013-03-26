import json
import trunk
import trunk.utils

from django.db import close_connection
from django.conf import settings
from django_sse.views import BaseSseView


PG_CONNECTION_KWARGS = getattr(
        settings,
        'POSTGRES_SSEQUEUE_CONNECTION_SETTINGS',
        settings.DATABASES['default']
)
PG_DEFAULT_CHANNEL = getattr(
        settings, 
        'POSTGRES_SSEQUEUE_CHANNEL_NAME',
        'sse'
)


class PostgresQueueView(BaseSseView):
    pg_channel = PG_DEFAULT_CHANNEL

    def iterator(self):
        # Close Django DB connection that handled auth query,
        # so it doesn't stay open until the end of the request
        # while SSEs are sent.
        close_connection()

        connection = _connect()
        connection.listen(self.get_pg_channel())

        # Only send 3 messages, then close connection and
        # rely on client reconnecting. Otherwise, Postgres
        # connections never close and continue to pile up.
        for i in range(3):
            for _, message in connection.notifications():
                event, data = json.loads(message)
                self.sse.add_message(event, data)
                yield
                break
        connection.close()

    def get_pg_channel(self):
        return self.pg_channel


def _connect():
    db = PG_CONNECTION_KWARGS
    dsn = trunk.utils.build_dsn(
            hostname=db['HOST'],
            port=db['PORT'],
            username=db['USER'],
            password=db['PASSWORD'],
            path=db['NAME'],
    )
    return trunk.Trunk(dsn)


def send_pg_event(event_name, data, channel=PG_DEFAULT_CHANNEL):
    connection = _connect()
    connection.notify(channel, json.dumps([event_name, data]))
    connection.close()


__all__ = ['send_pg_event', 'PostgresQueueView']

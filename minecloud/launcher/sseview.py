import gevent
import json
import time

from django import db
from django.core.cache import cache
from django_sse.views import BaseSseView


class SseView(BaseSseView):

    timeout = 30

    def iterator(self):
        # Close Django DB connection that handled auth query,
        # so it doesn't stay open until the end of the request
        # while SSEs are sent.
        db.close_connection()

        # Send keepalive here, rather than use Celery scheduled task.
        self.sse.add_message('keepalive', 'ping')
        yield

        start_time = time.time()
        default = json.dumps(['reload', str(start_time)])

        # Use timeout to end request, and rely on client to reconnect.
        with gevent.Timeout(self.timeout, False):
            while True:
                item = cache.get('last_updated', default)
                key, value = json.loads(item)
                last_updated = float(value)
                if last_updated > start_time:
                    start_time = last_updated
                    self.sse.add_message(key, value)
                    yield
                time.sleep(3)


def send_event(event_name, data=None, key='last_updated'):
    if not data:
        data = time.time()
    value = json.dumps([event_name, str(data)])
    cache.set(key, value)

__all__ = ['send_event', 'SseView']

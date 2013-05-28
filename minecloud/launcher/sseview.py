import json
import time

from django import db
from django.core.cache import cache
from django_sse.views import BaseSseView


class SseView(BaseSseView):

    def iterator(self):
        # Close Django DB connection that handled auth query,
        # so it doesn't stay open until the end of the request
        # while SSEs are sent.
        db.close_connection()

        # Set default, in case cache is empty
        default = json.dumps(['instance_state', 'terminated'])

        while True:
            item = cache.get('instance_state', default)
            key, value = json.loads(item)
            self.sse.add_message(key, value)
            yield
            time.sleep(3)


def send_event(event_name, data, key='instance_state'):
    value = json.dumps([event_name, data])
    cache_timeout = 60*60*24*365    # One year
    cache.set(key, value, cache_timeout)

__all__ = ['send_event', 'SseView']

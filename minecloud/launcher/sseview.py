import json
import time

from django import db
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

try:
    from django.http import StreamingHttpResponse as HttpResponse
except ImportError:
    from django.http import HttpResponse

from django_sse.views import BaseSseView
from sse import Sse


class SseView(BaseSseView):

    def __init__(self):
        self.sleep_interval = 3
        self.start_time = time.time()
        self.timeout = 30

    def __iter__(self):
        return self

    def next(self):
        running_time = time.time() - self.start_time
        if running_time >= self.timeout:
            raise StopIteration

        time.sleep(self.sleep_interval)

        # Set default, in case cache is empty
        default = json.dumps(['instance_state', 'terminated'])
        item = cache.get('instance_state', default)
        key, value = json.loads(item)
        self.sse.add_message(key, value)

        return "".join(self.sse)

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        # Close Django DB connection that handled auth query,
        # so it doesn't stay open until the end of the request
        # while SSEs are sent.
        db.close_connection()

        self.sse = Sse()

        self.request = request
        self.args = args
        self.kwargs = kwargs

        response = HttpResponse(self, content_type="text/event-stream")
        response['Cache-Control'] = 'no-cache'
        response['Software'] = 'django-sse'
        return response


def send_event(event_name, data, key='instance_state'):
    value = json.dumps([event_name, data])
    cache_timeout = 60*60*24*365    # One year
    cache.set(key, value, cache_timeout)

__all__ = ['send_event', 'SseView']

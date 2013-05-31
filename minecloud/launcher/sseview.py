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


class EventReader(object):
    """
    Iterator that yields events to be consumed by an SSE object.

    EventReader is a base class. To do anything useful, you must
    implement a read_events() method that will actually get events.
    Some possibile sources for events: polling memcache for updates,
    subscribing to a Redis Pub/Sub channel, listening for Postgres
    notifications.

    EventReader also provides options for:

        * Timout: Rather than providing an infinite stream of events,
          EventReader can raise StopIteration after a configurable
          timeout period.

        * Sleep interval: Setting sleep_interval allows for a pause
          between event readings. It's not necessary if you are listening
          for events, but it's useful if you are polling for updates.

    """
    def __init__(self, timeout=30, sleep_interval=3):
        self.start_time = time.time()
        self.timeout = timeout                  # In seconds, or None.
        self.sleep_interval = sleep_interval    # In seconds, or None.

    def read_events(self):
        """Customize this method to read events."""
        raise NotImplementedError

    def __iter__(self):
        for event, data in self.read_events():
            yield event, data

            if self.timeout:
                running_time = time.time() - self.start_time
                if running_time >= self.timeout:
                    self.close()
                    raise StopIteration

            if self.sleep_interval:
                time.sleep(self.sleep_interval)

    def close(self):
        """Clean up any connections here (DB, Redis, etc.)."""
        pass


class CacheReader(EventReader):
    """EventReader that fetches events by polling Django cache."""

    def __init__(self, key, default_value='', *args, **kwargs):
        self.key = key
        self.default_value = default_value
        super(CacheReader, self).__init__(*args, **kwargs)

    def read_events(self):
        while True:
            default = json.dumps([self.key, self.default_value])
            item = cache.get(self.key, default)
            event, data = json.loads(item)
            yield event, data


class SelfUpdatingSse(Sse):
    """
    Iterable object to be passed to StreamingHttpResponse.

    Though SelfUpdatingSse is derived from the Sse class, it is used
    differently. In the base Sse, __iter__() yields everything stored
    in the buffer, then stops. In SelfUpdatingSse, __iter__() will
    continually refresh its buffer by reading new events with
    self.event_reader and continually yield them.

    Because is yields all events, the SelfUpdatingSse object can itself be
    passed as the iterator to StreamingHttpResponse, rather than creating a
    separate iterator to read the events from the Sse object.

    Plus, we can add a close() method, which will allow us to clean up any
    connections necessary for reading events.

    """
    def __init__(self, event_reader, *args, **kwargs):
        self.event_reader = event_reader
        super(SelfUpdatingSse, self).__init__(*args, **kwargs)

    def __iter__(self):
        for event, data in self.event_reader:
            self.add_message(event, data)
            for item in self._buffer:
                yield item
            self.flush()

    def close(self):
        """
        This is called by the WSGI server at the end of the request and
        allows the reader to close any DB or Redis connections, as necessary.

        """
        self.event_reader.close()


class SseView(BaseSseView):

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        # Close Django DB connection that handled auth query,
        # so it doesn't stay open until the end of the request
        # while SSEs are sent.
        db.close_connection()

        reader=CacheReader(timeout=45, key='instance_state',
                           default_value='terminated')
        self.sse = SelfUpdatingSse(event_reader=reader)
        self.request = request
        self.args = args
        self.kwargs = kwargs

        response = HttpResponse(self.sse, content_type="text/event-stream")
        response['Cache-Control'] = 'no-cache'
        response['Software'] = 'django-sse'
        return response


def send_event(event_name, data, key='instance_state'):
    value = json.dumps([event_name, data])
    cache_timeout = 60*60*24*365    # One year
    cache.set(key, value, cache_timeout)

__all__ = ['send_event', 'SseView']

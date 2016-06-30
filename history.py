from twisted.internet.defer import inlineCallbacks

from autobahn.twisted.wamp import ApplicationSession
from autobahn.wamp.types import SubscribeOptions, PublishOptions

HISTORY_SESSION_EVENT_MAP = {}

# A Crossbar component for storing the last event sent across a channel. These
# events can be retrieved through the `meta.last_event` procedure call, passing
# the URI of the channel in question as a parameter.
#
# Currently, only the last event (one event) from the channel is remembered. As
# soon as another event passes through the channel, the last event will be
# replaced and can no longer be retrieved.
class HistorySession(ApplicationSession):
  @inlineCallbacks
  def onJoin(self, details):
    print("History session joined: {}".format(details))


    # Automatically subscribe to all topics so that all events can be stored.
    def store_message(*args, **kwargs):
      details = kwargs.pop('details')
      HISTORY_SESSION_EVENT_MAP[details.topic] = [args, kwargs]

    sub = yield self.subscribe(store_message, '.', options=SubscribeOptions(match=u'wildcard', details_arg='details'))
    print('Now tracking events from all topics.')


    # Register the `meta.last_event` remote procedure.
    def last_event(topic):
      return HISTORY_SESSION_EVENT_MAP.get(topic, 'no events available')

    reg = yield self.register(last_event, 'meta.last_event')
    print('Event history now available at `meta.last_event`.')

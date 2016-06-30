from collections import defaultdict

from twisted.internet.defer import inlineCallbacks

from autobahn.twisted.wamp import ApplicationSession
from autobahn.wamp.types import SubscribeOptions, PublishOptions


# The two-layer map of past events. The first layer identifies the topic on
# which the event was passed. The second layer identifies who sent the message.
# From here, a complete history of the last thing any publisher has done can be
# obtained.
HISTORY_SESSION_EVENT_MAP = defaultdict(lambda: {})


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
      HISTORY_SESSION_EVENT_MAP[details.topic][kwargs['originator']] = [args, kwargs]
      print('Got message from {} on {}'.format(kwargs['originator'], details.topic))

    sub = yield self.subscribe(store_message, '.', options=SubscribeOptions(match=u'wildcard', details_arg='details'))
    print('Now tracking events from all topics.')


    # Register the `meta.last_event` remote procedure.
    def last_event(topic, originator):
      print('Looking up last message from {} on {}'.format(originator, topic))
      return HISTORY_SESSION_EVENT_MAP.get(topic, {}).get(originator)

    reg = yield self.register(last_event, 'meta.last_event')
    print('Event history now available at `meta.last_event`.')

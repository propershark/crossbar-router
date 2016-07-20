from collections import defaultdict

from twisted.internet.defer import inlineCallbacks

from autobahn.twisted.wamp import ApplicationSession
from autobahn.wamp.types import SubscribeOptions, PublishOptions


# A map of lists for different object types. Each object type gets its own list
# of active objects. When a new object is activated, it will be added to the
# list of its type. When that object is deactivated, it will be removed from
# that list.
#
# The result is a list for each object type that represents the currently-
# active set of objects for that type.
ACTIVE_OBJECTS = defaultdict(dict)


# A Crossbar component for storing lists of active objects for an agency (realm).
# This component also handles the "Agency Topic" RPCs as defined in the wiki
# article linked below.
#
# See https://github.com/propershark/shark/wiki/WAMP-Events-and-RPCs#agency-topics
# for more information on these RPCs.
class AgencyRPCSession(ApplicationSession):
  @inlineCallbacks
  def onJoin(self, details):
    print("Agency RPC Session joined: {}".format(details))

    ACTIONS = defaultdict(lambda: lambda _, __, ___: "nothing")
    # Append the given object to the list of ACTIVE_OBJECTS under the given type.
    ACTIONS['activate']   = lambda typ, topic, obj: ACTIVE_OBJECTS[typ].update({ topic: obj })
    # Update the given object in the list of ACTIVE_OBJECTS under the given type.
    ACTIONS['update']     = lambda typ, topic, obj: ACTIVE_OBJECTS[typ].update({ topic: obj })
    # Remove the given object from the list of ACTIVE_OBJECTS under the given type.
    ACTIONS['deactivate'] = lambda typ, topic, obj: ACTIVE_OBJECTS[typ].pop(topic, None)

    # Subscribe to all vehicle topics and store their activations/deactivations.
    def vehicle_event(*args, **kwargs): ACTIONS[kwargs['event']]('vehicle', kwargs['details'].topic, args[0])
    # Subscribe to all station topics and store their activations/deactivations.
    def station_event(*args, **kwargs): ACTIONS[kwargs['event']]('station', kwargs['details'].topic, args[0])
    # Subscribe to all route topics and store their activations/deactivations.
    def route_event(*args, **kwargs):   ACTIONS[kwargs['event']]('route',   kwargs['details'].topic, args[0])


    # Subscribe to the appropriate channels based on type
    yield self.subscribe(vehicle_event, 'vehicles.', options=SubscribeOptions(match=u'prefix', details_arg='details'))
    print('Now tracking activations/deactivations on vehicle channels.')
    yield self.subscribe(station_event, 'stations.', options=SubscribeOptions(match=u'prefix', details_arg='details'))
    print('Now tracking activations/deactivations on station channels.')
    yield self.subscribe(route_event,   'routes.', options=SubscribeOptions(match=u'prefix', details_arg='details'))
    print('Now tracking activations/deactivations on route channels.')



    # Register the `agency.vehicles` rpc.
    def agency_vehicles(): return ACTIVE_OBJECTS['vehicle']
    # Register the `agency.vehicles` rpc.
    def agency_stations(): return ACTIVE_OBJECTS['station']
    # Register the `agency.vehicles` rpc.
    def agency_routes(): return ACTIVE_OBJECTS['route']

    reg = yield self.register(agency_vehicles,  'agency.vehicles')
    print('Active Vehicle list now available at `agency.vehicles`.')
    reg = yield self.register(agency_stations,  'agency.stations')
    print('Active Station list now available at `agency.stations`.')
    reg = yield self.register(agency_routes,    'agency.routes')
    print('Active Route list now available at `agency.routes`.')

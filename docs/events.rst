======
Events
======

PubMarine is used to pass events from the UI to the Dispatcher.  These are the
events that are emitted over the course of the program.  Events normally
report information about changes but we also use it as a general bus between
the frontend and backend to pass commands and return data as well.  This
allows the frontend and backend to operate asynchronously in some cases,
decouples the precise APIs from each other, and allows us to pass a single
PubPen object around to handle communication instead of having to pass
references to each object whose methods we wanted to invoke.

-----------
User events
-----------

User events return information about user objects.

.. py:function:: user.cash.update(new_cash: int, old_cash: int)

    Emitted when a change occurs in the amount of a user's cash on hand

    :arg int new_cash: The amount of cash a user now has
    :arg old_cash: The amount of cash the user had before

.. py:function:: user.login_success(username: string)

    Emitted when a user logs in successfully.

    :arg string username: The username that successfully logged in

.. py:function:: user.login_failure(msg: string)

    Emitted when a login attempt fails

    :arg string msg: A message explaining why the attempt failed

.. py:function:: user.info(username: string, cash: int, location: string)

    Emitted in response to a :py:func:`query.user.info`.  This comtains all
    relevant information about a user.

    :arg string username: The user who the information is about
    :arg int cash: The amount of cash the user has on their person
    :arg string location: The location that the user is in currently

.. py:function:: user.order_failure(msg: string)

    Emitted when an order attempt fails

    :arg string msg: A message explaining why the attempt failed


-----------
Ship Events
-----------

Ship events return information about ship objects.

.. py:function:: ship.cargo.update(amount_left: ManifestEntry, free_space: int, filled_hold: int)

    Emitted when a ship's cargo manifest changes (commodities are bought and
    sold or transferred to a warehouse)

    :arg ManifestEntry amount_left: A :class:`magnate.ship.ManifestEntry` that
        shows how much of a commodity is left on board.
    :arg int free_space: Amount of the hold that's free
    :arg int filled_hold: Amount of the hold that's filled

.. py:function:: ship.destinations(destinations: list)

    Emitted when the destinations a ship can travel to changes.  This usually
    means that the ship has moved to a new location which has different options.

    :arg list destinations: A list of strings showing where the ship can
        travel from here.

.. py:function:: ship.info(ship_type: string, free_space: int, manifest: dict of ManifestEntry)

    Emitted in response to a :py:func:`query.ship.info`.  This contains all
    relevant information about a ship.

    :arg string ship_type: The type of ship
    :arg int free_space: How much hold space is available
    :arg dict manifest: The commodities that are in the hold.  This is
        a dictionary of ManifestEntry types

.. py:function:: ship.moved(new_location: string, old_location: string)

    Emitted when a ship changes location.

    :arg string new_location: The location that the ship moved to
    :arg string old_location: The location that the ship moved from

.. py:function:: ship.movement_failure(msg: string)

    Emitted when a ship attempted to move but failed.

    :arg string msg: A message explaining why the movement failed


-------------
Market Events
-------------

Market events carry information about a specific market to the client.

.. py:function:: market.{location}.event(msg: string)

    Emitted when an event occurs at a market.  This is for informational
    purposes.  The client may choose to display the message for game flavour.

    :arg string msg: A message about the market

.. py:function:: market.{location}.info(prices: dict)

    Emitted in response to a :py:func:`query.market.{location}.info`.  This carries
    information about prices of all commodities in a market.

    :arg dict prices: A mapping of commodity name to its current price

.. py:function:: market.{location}.purchased(commodity: string, quantity: int)

    This contains information when a user successfully purchases a commodity
    at a specific market.

    :arg string commodity: The name of the commodity that was bought
    :arg int quantity: The amount of the commodity that was purchased

.. py:function:: market.{location}.sold(commodity: string, quantity: int)

    This contains information when a user successfully sold a commodity
    at a specific market.

    :arg string commodity: The name of the commodity that was sold
    :arg int quantity: The amount of the commodity that was sold

.. py:function:: market.{location}.update(commodity: string, price: int)

    Emitted when the price of a commodity changes.

    :arg string commodity: The name of the commodity being operated upon
    :arg string price: The new price of the commodity

-------------
Action Events
-------------

Action events signal the dispatcher to perform an action on behalf of the
user.

.. py:function:: action.ship.movement_attempt(destination: string)

    Emitted when the user requests that the ship be moved.  This can trigger
    a :py:func:`ship.moved` or :py:func:`ship.movement_failure` event.

    :arg string destination: The location to attempt to move the ship to

.. py:function:: action.user.login_attempt(username: string, password: string)

    Emitted when the user submits credentials to login.  This can trigger
    a :py:func:`user.login_success` or :py:func:`user.login_failure` event.

    :arg string username: The name of the user attempting to login
    :arg string password: The password for the user

.. py:function:: action.user.order(order: magnate.ui.event_api.Order)

    Emitted when the user requests that a commodity be bought from a market.
    Triggers one of :py:func:`market.{location}.purchased`, :py:func:`market.{location}.sold`, or
    :py:func:`user.order_failure`.

    :arg magnate.ui.event_api.Order order: All the details necessary to buy or sell
        this commodity.

    .. seealso:: :py:class:`magnate.ui.event_api.Order`


------------
Query Events
------------

These events are requests from the frontend for information from the backend.
This could simply be to get information during initialization or it could be
to resynchronize a cache of the values if it's noticed that something is off.

.. py:function:: query.cargo.info()

    Emitted to retrieve a complete record of the cargoes that are being
    carried in a ship.  This triggers a :py:func:`ship.cargo` event.

.. py:function:: query.market.{location}.info()

    Emitted to retrieve a complete record of commodities to buy and sell at
    a location.

.. py:function:: query.user.info(username: string)

    Emitted to retrieve a complete record of the user from the backend.

    :arg string username: The user about whom to retrieve information

.. py:function:: query.warehouse.{location}.info()

    Emitted to retrieve a complete record of the cargoes being held in
    a location's warehouse.


---------
UI Events
---------

UI events are created by a single user interface plugin for internal
communication.  For instance, a menu might want to communicate that a new
window needs to be opened and populated with data.  All UI events should be
namespaced under ``ui.[PLUGINNAME]`` so as not to conflict with other plugins.

Urwid Interface
===============

These are UI Events used by the Urwid interface.  Urwid has its own event
system but using it requires that the widget that wants to observe the event
must have a reference to the widget that emits it.  When dealing with a deep
hierarchy of widgets it can be painful to pass these references around so the
Urwid interface makes use of our pubmarine event dispatcher for some things.

[Currently None]

.. py:function:: ui.urwid.order_info(commodity: string, price: int)

    Emitted to inform the transaction dialog what commodity and price the user
    is interested in.

    :arg string commodity: Name of the commodity to buy or sell
    :arg int price: Price of the commodity


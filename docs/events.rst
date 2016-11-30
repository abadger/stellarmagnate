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

-----------
Ship Events
-----------

Ship events return information about ship objects.

.. py:function:: ship.destinations(destinations: list)

    Emitted when the destinations a ship can travel to changes.  This usually
    means that the ship has moved to a new location which has different options.

    :arg list destinations: A list of strings showing where the ship can
        travel from here.

.. py:function:: ship.moved(old_location: string, new_location: string)

    Emitted when a ship changes location.

    :arg string old_location: The location that the ship moved from
    :arg string new_location: The location that the ship moved to

.. py:function:: ship.movement_failure(msg: string)

    Emitted when a ship attempted to move but failed.

    :arg string msg: A message explaining why the movement failed

-------------
Action Events
-------------

Action events signal the dispatcher to perform an action on behalf of the
user.

.. py:function:: action.ship.movement_attempt(destination: string)

    Emitted when the user requests that the ship be moved.  This can trigger
    a :py:func:`ship.moved` or :py:func:`ship.movement_failure` event.

    :arg string destination: The location to attempte to move the ship to

.. py:function:: action.user.login_attempt(username: string, password: string)

    Emitted when the user submits credentials to login.  This can trigger
    a :py:func:`user.login_success` or :py:func:`user.login_failure` event.

    :arg string username: The name of the user attempting to login
    :arg string password: The password for the user

------------
Query Events
------------

These events are requests from the frontend for information from the backend.
This could simply be to get information during initialization or it could be
to resynchronize a cache of the values if it's noticed that something is off.

.. py:function:: query.user.info(username: string)

    Emitted to retrieve a complete record of the user from the backend.

    :arg string username: The user about whome to retrieve information

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

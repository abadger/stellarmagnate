.. image:: https://travis-ci.org/abadger/stellarmagnate.svg?branch=master
    :target: https://travis-ci.org/abadger/stellarmagnate

.. image:: https://coveralls.io/repos/github/abadger/stellarmagnate/badge.svg?branch=master
    :target: https://coveralls.io/github/abadger/stellarmagnate?branch=master

===============
Stellar Magnate
===============
:Author: Toshio Kuratomi <toshio@fedoraproject.org>
:Copyright: December 2016
:License: AGPLv3+

------------
Introduction
------------

In the late 1980s I played a game called `Planetary Travel
<https://archive.org/details/Big_Red_294_Planetary_Travel>`_ by `Brian
Winn <http://gel.msu.edu/winn/index.html>`_.  The game was a textual trading
game where you had to take a small amount of money and a space ship and travel
between the planets of our solar system to make money.

Stellar Magnate is a game written in that same genre but updated and enhanced.
Unlike the original Integer Basic that Planetary Travel was written in, this
is written in Python and makes use of asynchronous programming, abstractions
to allow multiple user interfaces, and other modern programming practices.

Stellar Magnate was written both to enjoy a little bit of nostalgia and to
have a practical problem on which to experiment with new technologies.  I hope
that the game is somewhat enjoyable and the core is simple enough that new
aspiring programmers can take a look at how it works to make it their own.

-----------
Limitations
-----------

If you're downloading the game at this point, you're sure to find that it is
somewhat lacking in features.  It is hosted on github as a cheap way to backup
the software, not because it's ready for widespread usage.  Currently, the
basic framework that separates the User Interface from the game's logic is in
place.  An `urwid <http://urwid.org/>`_ (text-based) interface is being
developed alongside the initial implementation of the game.

To log in, use the username "toshio" and any password.  The game currently
supports moving from planet to planet and buying and selling commodities on
those planets.  That's enough to be playable but it's far from fun at this
point.

The large TODO list includes:

* Finish the basic functionality which is encompassed in the DESIGN.urwid and
  MECHANICS files

  * Ability to buy/sell ship components
  * Banking system
  * Depreciation: Especially for ship equipment; commodities should get less
    valuable over time.
    * Necessary for equipment so that users can't sell initial equipment to
      make a quick buck in the beginning
    * For commodities, makes buying and holding slightly riskier than it
      already is.  Users need to pursue larger profit margins to make it
      worthwhile.

* Save and load of an in progress game
* When saving, use the username and password to store the file for
  a particular user
* Encounters: hostile ships, contraband, etc
* Advance the game play

  * A market system which fluctuates with time and location.
  * Client-server and multiplayer
  * New markets in other systems
  * Organize ships into fleets and automate fleet orders
  * Write a second, graphical UI.  Try to be different than the urwid UI to
    make sure that the UI concepts aren't leaking into the core engine.
  * Ability to buy/sell ships and manage fleets.  Instead of purchasing cargo
    modules, purchase different ships to build up a fleet.  Some ships
    increase cargo capacity; others increase defense against raiders.

* Some things that make it harder to make money

  * Pirates; pay off or fight off
  * License fees: Pay at the capital planet or be attacked by police
  * Contraband: Police attack you if they find you are carrying this
  * Maintenance fees

    * Docking charge
    * Fuel cost
    * Repair costs

  * Transit time

    * Outer planets take more time

      * Orbit data can be used to make this more interesting as well

* Client/Server
  * Game itself can be client/server easily but need to have ways in which
    gameplay is affected.  Do people get to attack each other?  An side trades
    happen?  Trade wars? Blockades?

===============
Stellar Magnate
===============
:Author: Toshio Kuratomi <toshio@fedoraproject.org>
:Copyright: December 2016
:License: AGPLv3+

------------
Introduction
------------

In the late 1980s I played a game called Planetary Travel by `Brian
Winn<http://gel.msu.edu/winn/index.html>`_.  The game was a textual trading
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
place.  An urwid (text-based) interface is slowly being written.

To log in, use the username "toshio" and any password.
The game currently supports moving from planet to planet.

The large TODO list includes:

* Finish the basic functionality which is encompassed in the DESIGN.urwid file
  * Ability to buy/sell commodities
  * Ability to buy/sell bigger ships
  * Ability to buy/sell ship components
  * A quick view of player/ship information
  * Banking system
* Save and load of an in progress game
* When saving, use the username and password to store the file for
  a particular user
* Events: market high and low prices
* Encounters: hostile ships, contraband, etc
* Advance the game play
  * A market system which fluctuates with time and location.
  * Client-server and multiplayer
  * New markets in other systems
  * Organize ships into fleets and automate fleet orders
  * Write a second, graphical UI.  Try to be different than the urwid UI to
    make sure that the UI concepts aren't leaking into the core engine.
* 

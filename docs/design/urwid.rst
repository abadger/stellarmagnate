Urwid UI
========

.. currentmodule:: magnate.ui.urwid

The Urwid UI backend is a text based backend.  It implements a series of static screens and menus
that the user interacts with to manage their fleet.

.. seealso:: Displaying on the console uses the `Urwid library <https://urwid.org>`_

Naming Conventions
------------------

Toplevel UI elements in the Urwid code are called Screens.  Most Screens are single area forms.  The
:class:`~main_screen.MainScreen` is the exception to this.  This complex Screen is composed of
various constant status windows displaying information to the user about their ship and
surroundings, a menubar to select options from and an area for contextual content which the user can
interact with.  The widgets displaying information are calld Windows and those that display the
contextual content are called Displays.

Each Display shows the user information upon which they can act.  For instance, the
:class:`~market_display.MarketDisplay` allows the user to select :class:`Commodities
<magnate.data.Commodity>` to buy and sell.

Sometimes a Display needs to popup a subelement that allows the user to input more information.
These widgets are named Dialogs.

Mockups
-------

Here there are various mockups of screens in the Urwid UI


Splash Screen
~~~~~~~~~~~~~

::

    +------------------------+
          Stellar Magnate
          1.0
          (c) Toshio Kuratomi
    +------------------------+


Status Bar
~~~~~~~~~~

This is part of the frame around the Main Window::

    +=Name: Hiormi -------------- Location: Earth -+


Menubar
~~~~~~~

This is the top level user interaction for the Main Window::

    +-------------------------------------------------------------------+
    | (P)ort District  Ship(Y)ard  (F)inancial  (T)ravel  (M)enu        |
    +-------------------------------------------------------------------+


Travel Display
~~~~~~~~~~~~~~

This is simply a text menu that allows the user to choose a destination planet::

    +-----------------------+
    | (1) Mercury
    | (2) Venus
    | (3) Earth
    | (4) Luna
    | (5) Mars
    | (6) Jupiter
    | (7) Saturn
    | (8) Uranus
    | (9) Neptune
    | (0) Pluto
    |
    | (!) Jump
    +-----------------------+



Menu Dialog
~~~~~~~~~~~

The Menu Dialog lets the user perform out-of-character functions like quitting the game::

    +----------+
    | (s)ave
    | (l)oad
    | (q)uit
    | (c)ontinue
    +----------+


Market Display
~~~~~~~~~~~~~~

Displays :class:`Commodities <magnate.data.Commodities>` that the user can buy and sell to turn a profit::

    +- Commodity -- Price - Quantity --- Hold ------ Warehouse --+
    | (1) Grain     $10     7.5E+200     7.5E+200    7.5E+200
    | (2) Metal     $100    1.7E+5       10          100
    | (3) Weapons   $2000   3.4E+21      1000        0
    | (4) Drugs     $10.1K  2.0E+10      10          0
    +------------------------------------------------------------+


Cargo Order Dialog
~~~~~~~~~~~~~~~~~~

The Cargo Order Dialog lets the user input quantities of a :class:`~magnate.data.Commodity` that
they wish to buy or sell.  The Dialog has a way to toggle between buying or selling the commodity.


Buy Mode::

    +------------------------+
    | (o) Buy ( ) Sell
    | Hold: XXX  Warehouse: YYY
    | Total cost: $XXX
    | hold/warehouse   (H)/(W)
    | Quantity [_____] [MAX]
    +------------------------+


Sell Mode::

    +------------------------+
    | ( ) Buy (o) Sell
    | Hold: XXX  Warehouse: YYY
    | Total sale: $XXX
    | Quantity [_____] [MAX]
    +------------------------+


Port Display
~~~~~~~~~~~~

We will eventually have distinct types of ships to buy and sell but for the initial release we'll
just adopt the |Planetary Travel| style of having a spaceship that we can buy additional cargo
modules for.  The Port Display lets the user buy equipment (additional cargo modules, warehouse
space, shipboard weapons, etc)::

    +- Equipment -------- Price --- Current --+
    | (1) Cargo Space     $10K     1000
    | (2) Lasers          $5000       1
    | (3) Warehouse       $15K    20000
    +-----------------------------------------+

Equipment Order Dialog
~~~~~~~~~~~~~~~~~~~~~~

The Equipment Order Dialog lets the user fill in additional information for buying equipment for
their ship::

    +------- Hold space - $42 ---+
    | Total Sale: $0
    | (o) Buy (o) Sell
    | Current Amount:
    | [MAX] Quantity [_____]
    |              [Place Order][Cancel]
    +------------------------+

Info Window
~~~~~~~~~~~

The Info Window sits alongside the Display in the Main Screen and shows an overview of statistics
about the player and ship::

    +-----------------+
    | Ship:
    |   Minnow
    | Type:
    |   Freighter
    | Free Space:
    |   1000
    | Cargo:
    |   500
    | Warehouse:
    |   10000
    | Transshipment:
    |   10
    | Bank:
    |   $1K
    | Cash:
    |   $1.5Mil
    | Loan:
    |   $0
    |
    +-----------------+


Financial Display
~~~~~~~~~~~~~~~~~

This allows the user to deposit money and take out loans::

    +-----------------+
    | (1) The Syndicate
    | (2) Solarian National Bank
    | (3) First Terran Bank and Trust
    | (4) Mercury Savings and Loan
    +-----------------+

:The Syndicate: Mob; high limit; high interest loan.  Present anywhere.  Deposit: low interest, 100%
                safe, but may be 0-50% inaccessible at any given time
:System-wide bank:  May not be present on pirate world.  std loan. Deposit: low interest, Safe
                    unless war.
:Capital planet bank: Available on subset of system worlds. May open/close branches. std loan.
                      Deposit moderate interest.  Sometimes bankrupts but bailout 75-95%.  War, may
                      lose all
:Planetary bank: Available 1 world. low interest loan. Deposit moderate interest.  Sometimes
                 bankrupts.  bailout 0-50%.  War, may lose all.

Financial Dialog
~~~~~~~~~~~~~~~~

Allows the user to select what they want to do at the financial institution they selected::

    +--------------+
    | (d)eposit
    | (w)ithdraw
    | (i)ncrease loan
    | (r)epay loan
    +--------------+

Ship Update
~~~~~~~~~~~

These are some thoughts on how to change the Ships for later versions

Fleet
^^^^^

::

    +------------+
    | (s)hip
    | (w)eapons
    +------------+

Ship
^^^^

::

    +- (B)uy ---------------+- (S)ell -----------+
    |                       |
    | (1) Scout [x2]  $1K   | (1) Tug [x3]        $1K
    | (2) Tug   [x1]  $1.2K | (2) Freighter [x1]  $500
    | (3) Freighter   $1.3K |
    | (4) Cruiser     $1M   |
    | (5) Carrier     $8T   |
    +-----------------------+--------------------+

Purchase Ship
^^^^^^^^^^^^^

::

    +------------------------+
    | Ship Type: Scout
    | Cargo:  100
    | Weapon Space:  5
    | Upkeep:  $20K/yr
    | Cost per: $1,000
    | Supply 3
    |
    | Total cost: $XXX
    | Purchase Quantity [_____] [MAX]
    +------------------------+

Weapons
^^^^^^^

::

    +- (B)uy----------------+--- (S)ell ------------+
    | (1) Laser [x10] $1K   |  (1) Laser [x2] $500
    +-----------------------+-----------------------+

Purchase Weapons
^^^^^^^^^^^^^^^^

::

    +------------------------+
    | Weapon Type: Laser
    | Space:  5
    | Upkeep:  $1K/yr
    | Cost per: $1,000
    | Supply: 10
    |
    | Total cost: $XXX
    | Quantity [_____] [MAX]
    +------------------------+

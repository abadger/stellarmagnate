This document describes the game mechanics

Market
======

Current
-------

Random pricing based upon a normal distribution.

Future
------
Need a cyclical market pricing.  This way prices rise or fall for a certain
duration.  This makes the user take more care to judge whether the item's
price is on its way up or down.

Cycle should be mostly time based so that we can recalculate the price when
a ship actually lands there rather than for every tick.

Will need to save the current state of the market so that loading a game
starts in the same place.

* Markets only have so many goods that they're willing to buy or sell
* Markets should be rated for population, industrialization, agriculture,
  mining.  These affect supply and demand of categories of goods.
* Markets will accept categories of product even if they don't sell them.
  * Supply and demand drives prices.  So if a market does not sell an item,
    there will be a low supply.  However, demand needs to be based off of how
    different it is from what is already there.
    * So perhaps categories need to be hierarchical.  The farther away on the
      hierarchy from something already sold, the less demand



Ship
====

Current
-------

* Purchase more cargo space

Future
------

* Purchase different ships
* Each ship that you can purchase has different characteristics

Fleets
~~~~~~

* We can organize ships into separate fleets
* Can send fleets off to trade in different locations
* Give fleets different orders about buying and selling


Finances
========

Current
-------

One bank.  Accessible whenever the user is on Earth.

Future
------

Multiple banks.

* The Syndicate:
  * Can do business everywhere
  * Loans money
  * High interest rates
  * Deposit low interest rate
  * 100% safe
  * May be inaccessible 50% of the time but never twice in a row
* System wide bank -- Solarian National Bank
  * May not be present on pirate worlds.
  * Standard loans
  * Deposit low-medium interest 
  * Safe unless war
* Capital planet bank -- First Terran Bank and Trust
  * Available on a subset of system worlds
  * May open/close branches.  Pick X% most industrial/civilized in-system worlds.
  * May sometimes bankrupts but bailout 75-95% of owed money
  * standard loan
  * moderate interest
  * War may lose all
* Planetary bank -- Mercury Savings and Loan
  * Available 1 world
  * Low interest loans
  * Deposits moderate interest
  * Sometimes bankrupts bailout 0-50%
  * War may lose all

Movement
========

Current
-------
Travelling from one location to another constitutes one turn

Future
------

* Markets have distances associated with them.  takes longer to travel from
  Mercury to Pluto than it does to travel from Venus to Earth
* Orbits?  Planets change positions?
* Fuel costs to travel


Combat
======

Current
-------

* Compare number of enemies with number of weapons
* Weapons hit X enemies per turn
* Enemies cause X damage per turn

Future
------

* Different ships can protect in differing amounts
* Different ships have different speeds
* Order ships on a grid
* Enemies encounter the grid of ships

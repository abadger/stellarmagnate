#
# Stellar Magnate - A space-themed commodity trading game
# Copyright (C) 2016, Toshio Kuratomi <toshio@fedoraproject.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import json

import attr

ALL_DESTINATIONS = ('Sol Research Station', 'Mercury', 'Venus', 'Earth',
                    'Luna', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto')

# Will get this from a file later
USER = '''
{"username": "toshio",
"cash": 500,
"ship": "Pigeon",
}
'''

SHIP = '''
{"type": "Passenger",
"name": "Pigeon",
"hold_space": 50,
"location": "Earth",
"cargo": {
    "name": "Food",
    "quantity": 10
    }
}
'''

# 1) Static data that defines commodities
#    These are bases upon initialization.
#    Should be kept in some format that's easy for humans to write
#    Can be transformed at packaging-time or build-time to avoid runtime
#    overhead and dependencies.
# 2) An instantiated Commodity.  Loaded with data from the static data file
#    Has a name and such
# 3) A list of instantiated Commodities.  Each market has a list of
#    commodities
# 4) A save file.  Has several markets and each one has a list of commodities


def load_user(data):
    user_data = json.loads(USER)
    return user_data

class User:
    """A logged in user"""
    def __init__(self, pubpen, username):
        self.pubpen = pubpen
        self.user = load_user(username)
        self.username = username
        self.cash = 500
        self.ship = Ship(pubpen)

        self.pubpen.subscribe('query.user.info', self.handle_user_info)

    def handle_user_info(self):
        """Return all information about a user

        :event user.info: All the information about the user
        """
        self.pubpen.publish('user.info', self.username, self.cash,
                            self.ship.location)


@attr.s
class ShipData:
    class_name = attr.ib(validator=attr.validators.instance_of(str))
    hold_space = attr.ib(validator=attr.validators.instance_of(int))


class Ship:
    """A user's ship"""
    def __init__(self, pubpen, ship, location='Earth'):
        self.pubpen = pubpen
        self._location = None
        self.ship = ship
        self._destinations = []
        self.location = location

        self.pubpen.subscribe('action.ship.movement_attempt', self.handle_movement)

    @property
    def location(self):
        """Retrieve the ship's location"""
        return self._location

    @location.setter
    def location(self, location):
        """Move the ship to a new location

        :arg location: The location to move to
        :event ship.moved: Emitted when the ship arrives at a new location
            :arg old_location: The location the ship moved from
            :arg location: The location the ship arrived at
        :event ship.destination: Emitted when the ship ship arrives at a new
            location
        :raises ValueError: when the new location is not valid
        """
        temp_destination = list(ALL_DESTINATIONS)
        temp_destination.remove(location)
        self._destinations = temp_destination

        self.pubpen.publish('ship.destinations', self.destinations)
        self.pubpen.publish('ship.moved', self._location, location)
        self._location = location

    @property
    def destinations(self):
        """Read-only property lists the ship's valid destinations"""
        return self._destinations

    def handle_movement(self, location):
        """Attempt to move the ship to a new location on user request

        :arg location: The location to move to
        :event ship.movement_failure: Emitted when the dhip could not be moved
            :msg: Unknown destination
            :msg: Ship too heavy
        """
        try:
            self.location = location
        except ValueError:
            self.pubpen.publish('ship.movement_failure', 'Unknown destination')
            return


class Commodity:
    """
    Information about a commodity
    :name: Name of the commodity
    :base_price: middle of the road for the commodity
    :fluctuation: How much the price varies compared to the base price
    """
    def __init__(self, pubpen, name, base_price, std_deviation, bonus):
        self.pubpen = pubpen

        self.name = name
        self.base_price = base_price
        self.std_deviation = std_deviation
        self.bonus = bonus

# JSON string defining base commodity values.  Going to push this to an
# external file/save file later
COMMODITIES = '''
{
    "food": [25, 10, ["Water shortage reduces food supply", 50], ["Algae farms have unexpected growth spurt", 1]],
    "metal": [67, 7.5, ["Smeltery breaks down, iron production slows", 100], ["New iron mine yields huge amounts of ore", 30]]
}
'''
class MarketCommodity:
    """
    Each commodity in a market has additional attributes:
    :current_price: current price of the commodity

    Eventually we want better price simulation.
    Factors:
        * Volume change.
            * Amount of commodity bought on world drives price up
            * Amount of commodity sold on world drives price down
            * These are weighted against the absolute volume of production,
              consumption, and trading on the world:
                * Amount of commodity produced on world drives price down
                * Amount of commodity consumed on world drives prices up
        * market fluctuation
            * Instead of randomly choosing a price, make the price fluctuate
              on a curve with random variation on the curve.  So prices will
              trend in an upward or downward direction for a while.
            * Some subset of historical pricing helps to inform new prices.
        * inflation
            * The value of goods should slowly increase over time and the value of money decrease
        * Events.
            * Random events cause prices to spike or fall.  These can help to
              establish a new normal for the price.

        Current, random price algorithm is based on a normal distribution:
            * Each commodity has a mean_price and a standard_deviation
            * Take a random number from 1-1000
            * 1-340 price calculated as random number within range mean to mean + standard deviation (34%)
            * 341-680 price calculated as random number within range mean to mean - standard deviation (34%)
            * 681-815 price calculated as random number between mean + one and mean + two standard deviations (13.5%)
            * 816-950 price calculated as random number between mean - one and mean - two standard deviations (13.5%)
            * 951-975 price is a positive event mean + two standard deviation + bonus (2.5%)
            * 976-1000 price is a negative event mean - two standard deviations - bonus (2.5%)
            * Bell curve would be:
            * 34%, one std deviation higher, 34% on std deviation lower
            * 47.5%, two std deviation higher, 47.5% 2 std deviations lower
            * 49.35% three std deviations higher, 49.35%, three std deviations lower

        Food: varies from
        1-50
        1 is event, 50 is event
        stdrange ~5-45
        So:
        * 25 is the mean,
        * std_dev = 10

    """
    def calculate_price(self):
        choose_range = random.randint(1, 100)
        price_decrease = bool(random.randint(0, 1))

        if choose_percentage >=1 and choose_percentage <= 68:
            adjustment = random.randint(0, self.std_deviation)
        elif choose_percentage >= 69 and choose_percentage <= 95:
            adjustment = random.randint(self.std_deviation, self.std_deviation * 2)
        else:
            adjustment = self.event_pricing

        if price_decrease:
            adjustment = -adjustment

        # Make sure price has a minimum value of 1
        price = self.base_price + adjustment
        if price < 1:
            price = 1

        self.current_price = 1
        self.pubpen.publish('market_update', self.name, self.current_price)

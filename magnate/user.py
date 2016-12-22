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
            :arg location: The location the ship arrived at
            :arg old_location: The location the ship moved from
        :event ship.destination: Emitted when the ship ship arrives at a new
            location
        :raises ValueError: when the new location is not valid
        """
        temp_destination = list(ALL_DESTINATIONS)
        temp_destination.remove(location)
        self._destinations = temp_destination

        self.pubpen.publish('ship.destinations', self.destinations)
        self.pubpen.publish('ship.moved', location, self._location)
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

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
"""
Dispatcher manages the communication between the backend and various user
interfaces.
"""


ALL_DESTINATIONS = ('Sol Research Station', 'Mercury', 'Venus', 'Earth',
                    'Luna', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto')

class Dispatcher:
    """Manage the communication between the backend and frontends"""


    def __init__(self, pubpen):
        self.pubpen = pubpen
        self.user = None

        self.pubpen.subscribe('action.user.login_attempt', self.login)

    def login(self, username, password):
        """Log a user into the game"""
        if 'toshio' in username.lower():
            self.user = User(self.pubpen, username)
            self.pubpen.publish('user.login_success', username)
        else:
            self.pubpen.publish('user.login_failure',
                                'Unknown account: {}'.format(username))


class User:
    """A logged in user"""
    def __init__(self, pubpen, username):
        self.pubpen = pubpen
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


class Ship:
    """A user's ship"""
    def __init__(self, pubpen, location='Earth'):
        self.pubpen = pubpen
        self._location = None
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

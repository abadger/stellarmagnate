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


class Dispatcher:
    """
    The dispatcher has methods which allow the UI to request actions be taken
    It communicates changes to the UI via pubmarine events.

    # Emitted events:
    #
    # :event: market.price_change
    # :args:
    #   * item_name
    #   * location
    #   * old_price
    #   * new_price
    #
    # :event: market.commodity_bought
    # :args:
    #   * item_name
    #   * location
    #   * who_bought
    #   * amount_bought
    #   * money_spent
    #
    # :event: market.commodity.sold
    # :args:
    #   * item_name
    #   * location
    #   * who_sold
    #   * amount_sold
    #   * money_received
    #
    # :event: ship.moved
    # :args:
    #   * old_location
    #   * new_location
    # :kwargs:
    #
    # :event: ship.destinations
    # :args:
    #   * destinations (list)
    #
    # :event: user.info
    # :args:
    #   * username
    #   * cash
    #   * location
    #
    # :event: user.login_success
    # :args:
    #   * username
    #
    # :event: user.login_failure
    # :args:
    #   * username
    #   * failure message
    #

    # Received signals
    # ================
    # In general, the dispatcher will receive and process action.* signals
    # from the controller.
    #
    # :event: action.user.login_attempt
    # :args:
    #   * username
    #   * password
    #
    # :event: action.ship.movement_attempt
    #   * ship_id
    #   * destination
    #
    #


    """


    def __init__(self, pubpen):
        self.pubpen = pubpen
        self.user = None

        self.pubpen.subscribe('action.user.login_attempt', self.login)

    def login(self, username, password):
        if 'toshio' in username.lower():
            self.pubpen.emit('user.login_success', username)
        else:
            self.pubpen.emit('user.login_failure', 'Unknown account: {}'.format(username))
        self.user = User(self.pubpen, username)

    def move(self, what, old_location, new_location):
        pass
        account = lookup(what)
        verify_account_at(old_location)
        verify_can_move(old_location, new_location)
        try:
            backend.move(account, new_location)
        except:
            yield old_location, error
        else:
            yield new_location


class User:
    def __init__(self, pubpen, username):
        self.pubpen = pubpen
        self.username = username
        self.cash = 500
        self.ship = Ship(pubpen)

        self.pubpen.subscribe('query.user.info', self.handle_user_info)

    def handle_user_info(self):
        self.pubpen.emit('user.info', self.username, self.cash, self.ship.location)


ALL_DESTINATIONS = ('Sol Research Station', 'Mercury', 'Venus', 'Earth', 'Luna', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto')

class Ship:
    def __init__(self, pubpen, location='Earth'):
        self.pubpen = pubpen
        self._location = None
        self.location = location

        self.pubpen.subscribe('action.ship.movement_attempt', self.handle_movement)

    @property
    def location(self):
        return self._location

    @location.setter
    def location(self, location):
        self.destinations = list(ALL_DESTINATIONS)
        self.destinations.remove(location)

        self.pubpen.emit('ship.destinations', self.destinations)
        self.pubpen.emit('ship.moved', self._location, location)
        self._location = location

    def handle_movement(self, location):
        try:
            self.location = location
        except ValueError:
            self.pubpen.emit('ship.movement_failure', 'Unknown destination')
            return


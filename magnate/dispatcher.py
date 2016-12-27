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

from .dataloader import load_data_definition


ALL_DESTINATIONS = tuple()


class Dispatcher:
    """Manage the communication between the backend and frontends"""

    def __init__(self, pubpen):
        self.pubpen = pubpen
        self.user = None
        self.markets = None
        self.ship_list = None

        self.pubpen.subscribe('action.ship.movement_attempt', self.handle_movement)
        self.pubpen.subscribe('action.user.login_attempt', self.login)
        self.pubpen.subscribe('action.user.order', self.handle_order)

    def login(self, username, password):
        """Log a user into the game"""
        if 'toshio' in username.lower():
            self.pubpen.publish('user.login_success', username)
            # Game can begin in earnest now
            self.markets, self.ship_list = load_data_definition(self.pubpen, 'stellar.yml')

            ### FIXME: In the future a ship should know what location it is
            # at.  And then it should be able to lookup what locations it can
            # reach from that planet.
            global ALL_DESTINATIONS
            ALL_DESTINATIONS = tuple(m for m in self.markets)
            self.user = User(self.pubpen, username)
            self.user.ship = Ship(self.pubpen, self.ship_list['Passenger'])
        else:
            self.pubpen.publish('user.login_failure',
                                'Unknown account: {}'.format(username))

    def handle_order(self, order):
        fatal_error = False

        # Check that the user is in the location
        if order.location != self.user.ship.location:
            fatal_error = True
            self.pubpen.publish('user.order_failure', msg='Cannot process an order when the player is not at the location')

        current_price = self.markets[order.location].prices[order.commodity]
        total_sale = current_price * (order.hold_quantity + order.warehouse_quantity)

        if order.buy:
            # Check that the price matches or is better
            if order.price < current_price:
                fatal_error = True
                self.pubpen.publish('user.order_failure', msg='Current market price is higher than on the order.  Refresh prices and try again')

            # Check that the user has enough cash
            if total_sale > self.user.cash:
                fatal_error = True
                self.pubpen.publish("user.order_failure", msg="Total amount of money for this sale exceeds the user's cash")

            # Purchase the commodity
            if not fatal_error:
                self.user.cash -= total_sale
                pass
                ### FIXME: add to the user's hold and warehouse space
                pass
                self.pubpen.publish('market.{}.purchased'.format(order.location), order.commodity, order.hold_quantity + order.warehouse_quantity)
        else:
            # Check that the price matches or is better
            if order.price > current_price:
                fatal_error = True
                self.pubpen.publish('user.order_failure', 'Current market price is lower than on the order.  Refresh prices and try again')
            ### FIXME: Check that the user has enough commodity
            pass

            # Report that the commodities were sold
            if not fatal_error:
                ### FIXME:  Deduct from the user's hold and warehouse space
                self.user.cash += total_sale
                self.pubpen.publish('market.{}.sold'.format(order.location), order.commodity, order.hold_quantity + order.warehouse_quantity)

    def handle_movement(self, location):
        """Attempt to move the ship to a new location on user request

        :arg location: The location to move to
        :event ship.movement_failure: Emitted when the dhip could not be moved
            :msg: Unknown destination
            :msg: Ship too heavy
        """
        try:
            self.user.ship.location = location
        except ValueError:
            self.pubpen.publish('ship.movement_failure', 'Unknown destination')
            return


from .ship import Ship

class User:
    """A logged in user"""
    def __init__(self, pubpen, username):
        self.pubpen = pubpen
        self.username = username
        self.cash = 500
        self.ship = None

        self.pubpen.subscribe('query.user.info', self.handle_user_info)

    def handle_user_info(self):
        """Return all information about a user

        :event user.info: All the information about the user
        """
        self.pubpen.publish('user.info', self.username, self.cash,
                            self.ship.location)

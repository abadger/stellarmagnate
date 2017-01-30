# Stellar Magnate - A space-themed commodity trading game
# Copyright (C) 2016-2017 Toshio Kuratomi <toshio@fedoraproject.org>
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

from .market import CommodityType
from .ship import ManifestEntry

class Dispatcher:
    """Manage the communication between the backend and frontends"""

    def __init__(self, magnate, markets):
        self.magnate = magnate
        self.pubpen = magnate.pubpen
        self.markets = markets
        self.user = None

        self.pubpen.subscribe('action.ship.movement_attempt', self.handle_movement)
        self.pubpen.subscribe('action.user.login_attempt', self.handle_login)
        self.pubpen.subscribe('action.user.order', self.handle_order)

    def handle_login(self, username, password):
        """
        Attempt to log the user into the game

        :arg username: User attempting to login
        :arg password: Password to authenticate with
        """
        user = self.magnate.login(username, password)
        self.user = user

    def handle_order(self, order):
        """
        Attempt to purchase or sell a commodity for the user

        :arg order: a :class:`magnate.order.Order` with all the
            relevant information to buy or sell the commodity
        :event user.order_failure: Emitted when the order could not be processed
        """
        fatal_error = False

        # Check that the user is in the location
        if order.location != self.user.ship.location.name:
            fatal_error = True
            self.pubpen.publish('user.order_failure',
                                'Cannot process an order when the player is not at the location')

        current_price = self.markets[order.location].commodities[order.commodity].price
        total_quantity = order.hold_quantity + order.warehouse_quantity
        total_sale = current_price * total_quantity

        if order.buy:
            # Check that the price matches or is better
            if order.price < current_price:
                fatal_error = True
                self.pubpen.publish('user.order_failure',
                                    "Current market price is higher than on the order."
                                    "  Refresh prices and try again")

            # Check that the user has enough cash
            if total_sale > self.user.cash:
                fatal_error = True
                self.pubpen.publish("user.order_failure",
                                    "Total amount of money for this sale exceeds the user's cash")

            if fatal_error:
                return

            # Purchase the commodity
            new_cash = self.user.cash - total_sale
            if CommodityType.cargo in self.markets[order.location].commodities[order.commodity].type:
                # Buy cargo
                new_cargo = ManifestEntry(order.commodity, order.hold_quantity, order.price)
                try:
                    self.user.ship.add_cargo(new_cargo)
                except ValueError:
                    self.pubpen.publish("user.order_failure",
                                        "Amount ordered, {}, will not fit into the"
                                        " ship's hold".format(order.hold_quantity))
                    return
                ### FIXME: add to the user's warehouse space
                pass
            else:
                # Buy Equipment
                if order.commodity.lower() == 'cargo module (100 units)':
                    self.user.ship.holdspace += total_quantity * 100
                    self.pubpen.publish('ship.equip.update', self.user.ship.holdspace)
                else:
                    ### TODO: handle warheouse and lasers
                    pass
                    self.pubpen.publish("user.order_failure",
                                        "Backend doesn't yet support buying {}".format(order.commodity))
                    return
            self.user.cash = new_cash
            self.pubpen.publish('market.{}.purchased'.format(order.location),
                                order.commodity, total_quantity)
        else:
            # Check that the price matches or is better
            if order.price > current_price:
                fatal_error = True
                self.pubpen.publish('user.order_failure',
                                    'Current market price is lower than on the order.'
                                    ' Refresh prices and try again')

            if fatal_error:
                return

            # Sell the commodities
            if CommodityType.cargo in self.markets[order.location].commodities[order.commodity].type:
                # Sell cargo
                try:
                    self.user.ship.remove_cargo(order.commodity, order.hold_quantity)
                except ValueError:
                    self.pubpen.publish('user.order_failure',
                                        'We do not have {} of {} on the ship to'
                                        ' sell'.format(order.hold_quantity, order.commodity))
                    return
                ### FIXME:  Deduct from the user's warehouse space
                pass
            else:
                # Sell Equipment
                if order.commodity.lower() == 'cargo module (100 units)':
                    try:
                        self.user.ship.holdspace -= total_quantity * 100
                    except ValueError:
                        fatal_error = True
                        self.pubpen.publish('user.order_failure',
                                            'We do not have {} of {} to'
                                            ' sell'.format(total_quantity, order.commodity))
                        return
                    self.pubpen.publish('ship.equip.update', self.user.ship.holdspace)
                else:
                    ### TODO: handle warehouse and lasers
                    pass
                    self.pubpen.publish("user.order_failure",
                                        "Backend doesn't yet support selling {}".format(order.commodity))
                    return

            self.user.cash += total_sale
            self.pubpen.publish('market.{}.sold'.format(order.location), order.commodity, total_quantity)

    def handle_movement(self, location):
        """Attempt to move the ship to a new location on user request

        :arg location: The location to move to
        :event ship.movement_failure: Emitted when the ship could not be moved
            :msg: Unknown destination
            :msg: Ship too heavy
        """
        try:
            self.user.ship.location = self.magnate.markets[location]
        except (ValueError, KeyError):
            self.pubpen.publish('ship.movement_failure', 'Unknown destination')
            return

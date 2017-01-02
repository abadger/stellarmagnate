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
Data structures related to Player controlled ships
"""
import attr


@attr.s
class ManifestEntry:
    """
    Associates a given amount of a commodity with sale-related information
    """
    #: Name of the commodity this ManifestEntry is for
    commodity = attr.ib(validator=attr.validators.instance_of(str))

    #: Amount of the commodity in this ManifestEntry
    quantity = attr.ib(validator=attr.validators.instance_of(int))

    #: Average price paid for the commodity.  This may be used to
    #: automatically show profit and loss
    price_paid = attr.ib(validator=attr.validators.instance_of(float), convert=float)

    # When we start using depreciation in price:
    #average_age = attr.ib(validator.attr.validators.instance_of(float))


@attr.s
class ShipData:
    """
    Base, static data on a type of ship
    """
    #: Name of the ship type ("Passenger", "Cruiser", etc)
    type = attr.ib(validator=attr.validators.instance_of(str))

    #: The average price of the ship
    mean_price = attr.ib(validator=attr.validators.instance_of(int))

    #: Measure of how widely the ship's price fluctuates
    standard_deviation = attr.ib(validator=attr.validators.instance_of(int))

    #: How quickly the resale value of the ship decreases
    depreciation_rate = attr.ib(validator=attr.validators.instance_of(int))

    #: How much space the ship has for cargo
    holdspace = attr.ib(validator=attr.validators.instance_of(int))

    #: How many weapons the ship can hold
    weaponmount = attr.ib(validator=attr.validators.instance_of(int))


class Ship:
    """A user's ship"""
    def __init__(self, magnate, ship_data, location):
        self.magnate = magnate
        self.pubpen = magnate.pubpen
        self.ship_data = ship_data

        self._location = None
        self._destinations = []

        self.manifest = {}
        self.filled_hold = 0

        self.location = location

        self.pubpen.subscribe('query.ship.info', self.handle_ship_info)

    def __getattr__(self, key):
        try:
            return super().__getattr__(self)
        except AttributeError:
            return getattr(self.ship_data, key)

    def handle_ship_info(self):
        """Publish information about the ship on request

        :event ship.info:
        """
        self.pubpen.publish('ship.info', self.type, self.holdspace,
                            self.filled_hold, self.filled_hold, self.manifest)

    def add_cargo(self, new_entry):
        """
        Add an amount of cargo to the hold

        :arg new_entry: A :class:`magnate.ship.ManifestEntry` which
            encapsulates the commodity being added to the hold.
        :raises ValueError: Raised when the quantity will not fit into the
            hold
        """
        if self.filled_hold + new_entry.quantity > self.holdspace:
            raise ValueError('Quantity will not fit in hold')

        if new_entry.commodity in self.manifest:
            entry = self.manifest[new_entry.commodity]
            entry.price_paid = (entry.price_paid * entry.quantity
                                + new_entry.price_paid * new_entry.quantity) \
                                / (entry.quantity + new_entry.quantity)
            entry.quantity += new_entry.quantity
        else:
            self.manifest[new_entry.commodity] = ManifestEntry(new_entry.commodity, new_entry.quantity, new_entry.price_paid)

        self.filled_hold += new_entry.quantity

        self.pubpen.publish('ship.cargo.update', self.manifest[new_entry.commodity], self.holdspace - self.filled_hold, self.filled_hold)

    def remove_cargo(self, commodity, amount):
        """
        Remove an amount of cargo from the hold

        :arg commodity: The commodity to remove
        :arg amount: The amount of the commodity to remove
        :rtype: :class:`magnate.ship.ManifestEntry`
        :return: Return the record of the commodity which is being removed
        :raises ValueError: Raised when there is not enough of the commodity
            currently in the hold
        """
        if not commodity in self.manifest or self.manifest[commodity].quantity < amount:
            raise ValueError('We do not have {} of {} in the hold'.format(amount, commodity))

        transfer = ManifestEntry(commodity, amount, self.manifest[commodity].price_paid)
        if amount == self.manifest[commodity].quantity:
            amount_left = ManifestEntry(commodity, 0, self.manifest[commodity].price_paid)
            del self.manifest[commodity]
        else:
            self.manifest[commodity].quantity -= amount
            amount_left = self.manifest[commodity]
        self.filled_hold -= amount

        self.pubpen.publish('ship.cargo.update', amount_left, self.holdspace - self.filled_hold, self.filled_hold)

        return transfer

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
        temp_destinations = [l for l in location.system.locations]
        try:
            temp_destinations.remove(location.name)
        except ValueError:
            # No worries, we just want to make sure we can't go to ourselves
            pass
        self._destinations = temp_destinations

        previous_location = self._location.name if self._location is not None else None
        self._location = location
        self.pubpen.publish('ship.destinations', self.destinations)
        self.pubpen.publish('ship.moved', location.name, previous_location)

    @property
    def destinations(self):
        """Read-only property lists the ship's valid destinations"""
        return self._destinations

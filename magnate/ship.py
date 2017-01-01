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

import attr

from . import dispatcher

@attr.s
class ShipData:
    type = attr.ib(validator=attr.validators.instance_of(str))
    holdspace = attr.ib(validator=attr.validators.instance_of(int))


@attr.s
class ManifestEntry:
    commodity = attr.ib(validator=attr.validators.instance_of(str))
    quantity = attr.ib(validator=attr.validators.instance_of(int))
    price_paid = attr.ib(validator=attr.validators.instance_of(float))
    # When we start using depreciation in price:
    #average_age = attr.ib(validator.attr.validators.instance_of(float))

class Ship:
    """A user's ship"""
    def __init__(self, pubpen, ship_data, location='Earth'):
        self.pubpen = pubpen
        self.ship_data = ship_data

        self.name = None
        self._location = None
        ### FIXME: Move this into the locations?
        self._destinations = []

        self.manifest = {}
        self.filled_hold = 0

        self.location = location

    def __getattr__(self, key):
        try:
            return super().__getattr__(self)
        except AttributeError:
            return getattr(self.ship_data, key)

    def add_cargo(self, new_entry):
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

    def remove_cargo(self, commodity, amount):
        if not commodity in self.manifest or self.manifest[commodity].quantity < amount:
            raise ValueError('We do not have {} of {} in the hold'.format(amount, commodity))

        transfer = ManifestEntry(commodity, amount, self.manifest[commodity].price_paid)
        if amount == self.manifest[commodity].quantity:
            del self.manifest[commodity]
        else:
            self.manifest[commodity].quantity -= amount
        self.filled_hold -= amount

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
        ### FIXME: Needto make this retrieve the destinations from the location
        temp_destination = list(dispatcher.ALL_DESTINATIONS)
        try:
            temp_destination.remove(location)
        except ValueError:
            # No worries, we just want to make sure we can't go to ourselves
            pass
        self._destinations = temp_destination

        self.pubpen.publish('ship.destinations', self.destinations)
        self.pubpen.publish('ship.moved', location, self._location)
        self._location = location

    @property
    def destinations(self):
        """Read-only property lists the ship's valid destinations"""
        return self._destinations
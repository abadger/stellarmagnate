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
Classes to model the Location and Markets in Stellar Magnate
"""

from collections import OrderedDict, abc
from enum import Enum
from functools import partial
import random

import attr

from .utils.attrs import (container_converter, container_validator,
                          enum_converter, enum_validator, sequence_of_type)


# What is the organization of this data?
#
# There is some data which does not vary between games.  These are base
# attributes about game objects.  Things like names of commodities and their
# price ranges.  These are read from a static data file and stored in
# a FooData class.  The FooData sometimes has a category associated with it.
# For instance, grain is a type of food.  These are expressed as a FooType
# Enum.  The enum_validator and enum_converter helper functions are used to
# store those in the FooData objects.
#
# The game also has variable data.  Things like player information and market
# prices.  This data is read from a save file.  The game has Foo classes which
# combine the variable information with the static information.  A Foo class
# has-a FooData rather than an is-a FooData so that the static information
# does not have to be copied with every instance.  A Foo class may have
# several different types of *Data class if that makes the most sense.  That's
# because the Foo classes are also the interface for the rest of the game to
# interact with both the variable and static data.

# Enums are class-like but here we are using the function interface for
# creating them so that we don't have to manually specify ids for each
# category
#pylint: disable=invalid-name
CommodityType = Enum('CommodityType', ('cargo',
                                       'ship',
                                       'food',
                                       'metal',
                                       'fuel',
                                       'low bulk chemical',
                                       'high bulk chemical',
                                       'low bulk machine',
                                       'high bulk machine',
                                       'equipment',
                                       'ship parts',
                                       'property',
                                      ))


LocationType = Enum('LocationType', ('star', 'planet', 'moon',
                                     'space station'))
#pylint: enable=invalid-name


@attr.s
class CommodityData:
    """
    An item that can be bought and sold.

    :name: Name of the commodity
    :type: A frozenset of categories that the commodity is in.  These can be any of :class:`CommodityType`
    :mean_price: The average price of the commodity
    :standard_deviation: One standard deviation of the price data
    :depreciation_rate: Rate at which the commodity depreciates in price.
        perishables and equipment depreciates at a higher rate than
        non-perishable goods
    :hold_space: How much hold space the item takes up
    :events: a list of special events that affect the pricing of this item
    """
    name = attr.ib(validator=attr.validators.instance_of(str))
    type = attr.ib(validator=partial(container_validator, abc.Set,
                                     not_container_type=abc.MutableSet,
                                     contained_validator=partial(enum_validator, CommodityType)),
                   convert=partial(container_converter, frozenset,
                                   contained_converter=partial(enum_converter, CommodityType)))
    mean_price = attr.ib(validator=attr.validators.instance_of(int))
    standard_deviation = attr.ib(validator=attr.validators.instance_of(int))
    depreciation_rate = attr.ib(convert=float, validator=attr.validators.instance_of(float))
    hold_space = attr.ib(convert=int, validator=attr.validators.instance_of(int))
    events = attr.ib(default=attr.Factory(list),
                     validator=attr.validators.optional(attr.validators.instance_of(list)))


class Commodity:
    """
    Composition saves memory.  We only need one copy of the CommodityData for
    the run but we need one copy of the Commodity in each Market that it
    appears.
    """
    def __init__(self, pubpen, commodity_data):
        self.pubpen = pubpen
        self._commodity_data = commodity_data

        self.price = None

    def __getattr__(self, key):
        try:
            return super().__getattr__(self)
        except AttributeError:
            return getattr(self._commodity_data, key)

    def __repr__(self):
        data_repr = self._commodity_data.__repr__()
        return data_repr +  ' price={}'.format(self.price)


@attr.s
class SystemData:
    """
    A stellar system in which to place locations
    """
    name = attr.ib(validator=attr.validators.instance_of(str))
    # Can't do better than object because we have to break the circular
    # relationship so we can define one of these before the other.
    locations = attr.ib(validator=attr.validators.optional(partial(sequence_of_type, object, 'immutable')))


@attr.s
class LocationData:
    """
    Location at which :class:`Commodities` can be bought and sold.

    :name: The name of the location
    :type: The type of location this is.  These can be any of :class:`LocationType`
    :system: The stellar system which the location is within
    """
    name = attr.ib(validator=attr.validators.instance_of(str))
    type = attr.ib(validator=partial(enum_validator, LocationType),
                   convert=partial(enum_converter, LocationType))
    system = attr.ib(validator=attr.validators.instance_of(SystemData))

    #def __attrs_post_init__(self, pubpen):
    #    pass


class Market:
    """
    Location at which :class:`Commodities` can be bought and sold.
    """
    def __init__(self, magnate, location_data, commodity_data):
        self.magnate = magnate
        self.pubpen = magnate.pubpen
        self.location = location_data
        self.commodities = commodity_data

        # Will be used for cyclic pricing
        #self.price_time = datetime.datetime.utcnow()

        self.recalculate_prices()
        self.pubpen.subscribe('query.market.{}.info'.format(self.location.name), self.handle_market_info)
        self.pubpen.subscribe('ship.moved', self.handle_movement)

    def __getattr__(self, key):
        try:
            return super().__getattr__(self)
        except AttributeError:
            return getattr(self.location, key)

    def handle_market_info(self):
        """
        Publish information about current prices

        :event market.{location}.info: Publishes the information about the
            current prices in the market
        """
        self.pubpen.publish('market.{}.info'.format(self.location.name), self.commodities)

    def handle_movement(self, new_location, *args):
        """Recalculate prices when the ship arrives at this location

        :arg new_location: The location that the ship has arrived at
        """
        if new_location == self.location.name:
            self.recalculate_prices()

    def recalculate_prices(self):
        """Set new prices for all the commodities in the market"""
        for commodity in self.commodities:
            self._calculate_price(commodity)

    def _calculate_price(self, commodity):
        """
        Calculates a new price for a commodity

        :arg commodity: The name of the commodity.

        Current, random price algorithm is based on a normal distribution:

        * Each commodity has a static mean_price and standard_deviation
        * 34% of the time, the price is between the mean and one std deviation higher
        * 34% of the time, the price is between the mean and one std deviation lower
        * 13.5% of the time, the price is between the mean + one std deviaiton
          and the mean and two std deviations higher
        * 13.5% of the time, the price is between the mean - one std deviaiton
          and the mean and two std deviations lower
        * 2.5% of the time, the price is a price-positive event
        * 2.5% of the time, the price is a price-negative event

        Example:

        * Food has a mean price of 25 and std_deviation of 10
        * 34% of the time food prices are between 25-35
        * 34% of the time food prices are between 15-25
        * 13.5% of the time food prices are between 35-45
        * 13.5% of the time food prices are between 5-15
        * 2.5% of the time food prices hit a positive event (food event is food price 50)
        * 2.5% of the time food prices hit a negative event (food event is food price 1)

        """
        # Eventually we want better price simulation.
        # Factors:
        #     * Volume change.
        #         * Amount of commodity bought on world drives price up
        #         * Amount of commodity sold on world drives price down
        #         * These are weighted against the absolute volume of production,
        #           consumption, and trading on the world:
        #             * Amount of commodity produced on world drives price down
        #             * Amount of commodity consumed on world drives prices up
        #     * market fluctuation
        #         * Instead of randomly choosing a price, make the price fluctuate
        #           on a curve with random variation on the curve.  So prices will
        #           trend in an upward or downward direction for a while.
        #         * Some subset of historical pricing helps to inform new prices.
        #     * inflation
        #         * The value of goods should slowly increase over time and the value of money decrease
        #     * Events.
        #         * Random events already cause prices to spike or fall.  Make these also help
        #           establish a new normal for the price.

        #now = datetime.datetime.utcnow()

        std_dev = self.commodities[commodity].standard_deviation
        mean_price = self.commodities[commodity].mean_price

        choose_percentage = random.randint(1, 100)
        price_decrease = bool(random.randint(0, 1))

        is_event = False
        if choose_percentage >= 1 and choose_percentage <= 68:
            adjustment = random.randint(0, std_dev)
        elif choose_percentage >= 69 and choose_percentage <= 95:
            adjustment = random.randint(std_dev, std_dev * 2)
        else:
            is_event = True
            for event in self.commodities[commodity].events:
                if price_decrease and event['type'] == 'sale':
                    price = mean_price - 2 * std_dev - event['adjustment']
                    break
                elif not price_decrease and event['type'] == 'shortage':
                    price = mean_price + 2 * std_dev + event['adjustment']
                    break
            else:
                # Our data is supposed to have a positive and negative event
                # for everything.  But handle this case in case our data is
                # bad.  User won't see a traceback but if we notice we can fix
                # it.
                price = mean_price
                event = {'type':  'error',
                         'adjustment': 0,
                         'msg': 'Production levels for {} were right on target'.format(commodity)
                        }
            self.pubpen.publish('market.event', self.location.name, commodity, price, event['msg'])

        if not is_event:
            if price_decrease:
                adjustment = -adjustment
            price = mean_price + adjustment

        # Make sure price has a minimum value of 1
        if price < 1:
            price = 1

        self.commodities[commodity].price = price
        self.pubpen.publish('market.{}.update'.format(self.location.name), self.commodities[commodity])

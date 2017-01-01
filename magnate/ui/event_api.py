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
Data structures used when communicating over the publish subscribe event
manager to the dispatcher.
"""

import enum
from functools import partial

import attr

from ..utils.attrs import enum_converter, enum_validator


# Enums are class-like but here we are using the function interface for
# creating them so that we don't have to manually specify ids for each
# category
#pylint: disable=invalid-name
OrderStatusType = enum.Enum('OrderStatusType', ('presale', 'submitted', 'rejected', 'finalized'))
#pylint: enable=invalid-name


@attr.s
class Order:
    """Information needed to complete a transaction.

    * :py:attr:`location` The location at which the sale is occuring
    * :py:attr:`commodity`: the name of the commodity being bought or sold
    * :py:attr:`price`: the price at which the user is agreeing to buy or sell
    * :py:attr:`hold_quantity`: The amount of the commodity to place in or
        take from the ship's hold
    * :py:attr:`warehouse_quantity`: The amount of the commodity to place in
        or take from the player's warehouse space at the location
    * :py:attr:`buy`: if True, the user is asking to buy the commodity.
        Otherwise, the user is selling the commodity
    * :py:attr:`status`: Status of the transaction.  May be any one of the EnumTypes
    """
    location = attr.ib(validator=attr.validators.instance_of(str))
    commodity = attr.ib(validator=attr.validators.instance_of(str))
    price = attr.ib(validator=attr.validators.instance_of(int))
    hold_quantity = attr.ib(validator=attr.validators.instance_of(int), default=0)
    warehouse_quantity = attr.ib(validator=attr.validators.instance_of(int), default=0)
    buy = attr.ib(validator=attr.validators.instance_of(bool), default=True)
    status = attr.ib(default=OrderStatusType.presale,
                     validator=partial(enum_validator, OrderStatusType),
                     convert=partial(enum_converter, OrderStatusType))

# Stellar Magnate - A space-themed commodity trading game
# Copyright (C) 2019 Toshio Kuratomi <toshio@fedoraproject.org>
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
.. py:function:: action.user.order(order: magnate.ui.event_api.Order)

    Emitted when the user requests that a commodity be bought from a market.
    Triggers one of :py:func:`market.{location}.purchased`, :py:func:`market.{location}.sold`, or
    :py:func:`user.order_failure`.

    :arg magnate.ui.event_api.Order order: All the details necessary to buy or sell
        this commodity.

    .. seealso:: :py:class:`magnate.ui.event_api.Order`

.. py:function:: query.user.info(username: string)

    Emitted to retrieve a complete record of the user from the backend.

    :arg string username: The user about whom to retrieve information

"""

from __main__ import magnate


def fulfill_order(order):
    pass


def get_user_data(username):
    pass


def register_event_handlers(pubpen):
    """Register event handlers"""
    pubpen.subscribe('action.user.order', fulfill_order)
    pubpen.subscribe('query.user.info', get_user_data)

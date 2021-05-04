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
.. py:function:: action.ship.movement(ship_id: int, destination: string)

    Emitted when the user requests that the ship be moved.  This can trigger
    a :py:func:`ship.moved` or :py:func:`ship.movement_failure` event.

    :arg string destination: The location to attempt to move the ship to

.. py:function:: query.cargo.info(ship_id: int)

    Emitted to retrieve a complete record of the cargoes that are being
    carried in a ship.  This triggers a :py:func:`ship.cargo` event.
"""

from __main__ import magnate


def move_ship(ship_id, destination):
    # Lookup ship_id in magnate.
    # Attempt to move it
    pass


def get_cargo_info(ship_id):
    pass


def register_event_handlers(pubpen):
    """Register event handlers"""
    pubpen.subscribe('action.ship.movement', move_ship)
    pubpen.subscribe('query.cargo.info', get_cargo_info)

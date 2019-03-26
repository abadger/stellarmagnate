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
*** Change so that location is a parameter
.. py:function:: query.warehouse.{location}.info()

    Emitted to retrieve a complete record of the cargoes being held in
    a location's warehouse.
"""

from __main__ import magnate


def get_warehouse_data(location):
    pass


def register_event_handlers(pubpen):
    """Register event handlers"""
    pubpen.subscribe('query.warehouse.info', get_warehouse_data)

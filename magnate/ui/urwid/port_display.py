# Stellar Magnate - A space-themed commodity trading game
# Copyright (C) 2017 Toshio Kuratomi <toshio@fedoraproject.org>
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
This handles the window where the user sells equipment for their ship
"""

from ...market import CommodityType
from .commodity_catalog import CatalogColumn, CommodityCatalog


class PortDisplay(CommodityCatalog):
    """Display for the user to manage their ship and equipment"""

    signals = ['close_port_display', 'open_equip_order_dialog']

    def __init__(self, pubpen):
        auxiliary_cols = [CatalogColumn('Price', 13, money=True),
                          #CatalogColumn('Amount', 20),
                          CatalogColumn('Currently Owned', 20),
                         ]

        #
        # Indexes to special columns
        #
        self.owned_col_idx = 1

        super().__init__(pubpen, 'ui.urwid.equip_order_info',
                         primary_title='Equipment', auxiliary_cols=auxiliary_cols,
                         price_col_idx=0, types_traded=frozenset((CommodityType.equipment,
                                                                  CommodityType.property)))

        #
        # Event handlers
        #
        self.pubpen.subscribe('ship.info', self.handle_ship_info)
        self.pubpen.subscribe('ship.cargo.update', self.handle_cargo_update)

    #
    # Handle updates to the displayed info
    #
    def handle_ship_info(self, ship_type, free_space, filled_space, *args): #pylint: disable=unused-argument
        """Update the display with total hold space owned"""
        self.auxiliary_cols[self.owned_col_idx].data_map['Cargo Module (100 units)'] = (free_space + filled_space) // 100
        self._construct_commodity_list(self.auxiliary_cols[self.owned_col_idx].data_map)

    def handle_cargo_update(self, cargo, free_space, filled_space): #pylint: disable=unused-argument
        """Update the display with total hold space owned"""
        self.auxiliary_cols[self.owned_col_idx].data_map['Cargo Module (100 units)'] = (free_space + filled_space) // 100
        self._construct_commodity_list(self.auxiliary_cols[self.owned_col_idx].data_map)

    def handle_new_warehouse_info(self, warehouse_info):
        """Update the equipment display with total warehouse space owned"""
        pass

    def handle_new_location(self, new_location, *args):
        """
        Update the market display when the ship moves

        :arg new_location: The location the ship has moved to
        """
        super().handle_new_location(new_location, *args)

        # Get holdspace info
        self.pubpen.publish('query.ship.info')
        pass
        ### TODO: events geared towards the equipment, not cargo
        # Sync up information
        #self.pubpen.subscribe('warehouse.{}.update'.format(new_location)) => handle new warehouse info
        #self.pubpen.publish('query.warehouse.{}.info'.format(new_location))

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
""" Handle the display of Markets and Commodities"""

from ...market import CommodityType
from .commodity_catalog import CatalogColumn, CommodityCatalog


class MarketDisplay(CommodityCatalog):
    """Display the market information to buy and sell commodities"""
    signals = ['close_market_display', 'open_cargo_order_dialog']

    def __init__(self, pubpen):
        auxiliary_cols = [CatalogColumn('Price', 13, money=True),
                          #CatalogColumn('Amount', 20),
                          CatalogColumn('Hold', 20),
                          CatalogColumn('Warehouse', 20),
                         ]

        #
        # Indexes to special columns
        #
        self.hold_col_idx = 1
        self.warehouse_col_idx = 2

        super().__init__(pubpen, 'ui.urwid.cargo_order_info',
                         primary_title='Commodity', auxiliary_cols=auxiliary_cols,
                         price_col_idx=0, types_traded=frozenset((CommodityType.cargo,)))

        #
        # Event handlers
        #
        self.pubpen.subscribe('ship.info', self.handle_ship_info)
        self.pubpen.subscribe('ship.cargo.update', self.handle_cargo_update)

    #
    # Handle updates to the displayed info
    #
    def handle_ship_info(self, ship_type, free_space, filled_space, manifest): #pylint: disable=unused-argument
        """
        Update the display with hold information for all commodities
        """
        for key, value in manifest.items():
            self.auxiliary_cols[self.hold_col_idx].data_map[key] = value.quantity
        self._construct_commodity_list(self.auxiliary_cols[self.hold_col_idx].data_map)

    def handle_cargo_update(self, cargo, *args):
        """Update the market display when cargo info changes"""
        self.auxiliary_cols[self.hold_col_idx].data_map[cargo.commodity] = cargo.quantity
        self._construct_commodity_list(self.auxiliary_cols[self.hold_col_idx].data_map)

    def handle_new_warehouse_info(self, warehouse_info):
        """Update the market display when warehouse info changes"""
        pass

    def handle_new_location(self, new_location, *args):
        """
        Update the market display when the ship moves

        :arg new_location: The location the ship has moved to
        """
        super().handle_new_location(new_location, *args)

        #self.pubpen.subscribe('warehouse.{}.update'.format(new_location)) => handle new warehouse info
        self.pubpen.publish('query.warehouse.{}.info'.format(new_location))

        # Ship info we keep constantly in contact with
        self.pubpen.publish('query.ship.info')

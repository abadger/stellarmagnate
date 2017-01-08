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

from collections import OrderedDict
from functools import partial

import urwid

from .indexed_menu import IndexedMenuButton, IndexedMenuEnumerator
from .numbers import format_number
from .sideless_linebox import SidelessLineBox


class MarketDisplay(urwid.WidgetWrap):
    """Display the market information to buy and sell commodities"""
    _selectable = True
    signals = ['close_market_display', 'open_order_dialog']

    def __init__(self, pubpen):
        self.pubpen = pubpen
        self.location = None
        self.commodities = []
        self.keypress_map = IndexedMenuEnumerator()
        self.commodity_idx_map = OrderedDict()
        self.commodity_price_map = OrderedDict()
        self.commodity_hold_map = OrderedDict()
        self._market_query_sub_id = None

        # Columns
        # LineBox w/ title and custom left/right sides
        # listboxes w/ listwalkers
        # if there's an onselect handler, set that so that we programatically
        # have selection highlight all three column?
        #

        self.commodity_list = urwid.SimpleFocusListWalker([])
        self.price_list = urwid.SimpleFocusListWalker([])
        #self.amount_list = urwid.SimpleFocusListWalker([])
        self.hold_list = urwid.SimpleFocusListWalker([])
        self.warehouse_list = urwid.SimpleFocusListWalker([])

        self.commodity = urwid.ListBox(self.commodity_list)
        self.price = urwid.ListBox(self.price_list)
        #self.amount = urwid.ListBox(self.amount)
        self.hold = urwid.ListBox(self.hold_list)
        self.warehouse = urwid.ListBox(self.warehouse_list)
        #pylint: disable=protected-access
        self.price._selectable = False
        #self.amount._selectable = False
        self.hold._selectable = False
        self.warehouse._selectable = False
        #pylint: enable=protected-access

        market_col = SidelessLineBox(self.commodity, title='Commodity', title_align='left',
                                     lline=None, tlcorner='─', trcorner='─',
                                     rline=None, blcorner='─', brcorner='─')
        price_col = SidelessLineBox(self.price, title='Price', title_align='left',
                                    trcorner='\u2500', rline=None,
                                    brcorner='\u2500', tlcorner='\u2500',
                                    lline=None, blcorner='\u2500')
        #amount_col = SidelessLineBox(self.amount, title='For Sale',
        #                             trcorner='\u2500', rline=None,
        #                             brcorner='\u2500', tlcorner='\u2500',
        #                             lline=None, blcorner='\u2500')
        hold_col = SidelessLineBox(self.hold, title='Hold', title_align='left',
                                   trcorner='\u2500', rline=None,
                                   brcorner='\u2500', tlcorner='\u2500',
                                   lline=None, blcorner='\u2500')
        warehouse_col = SidelessLineBox(self.warehouse, title='Warehouse', title_align='left',
                                        tlcorner='\u2500', lline=None, blcorner='\u2500',
                                        trcorner='\u252c', brcorner='\u2524')

        self.market_display = urwid.Columns([('weight', 2, market_col), (13, price_col), (20, hold_col), (20, warehouse_col)])

        super().__init__(self.market_display)

        self.pubpen.subscribe('ship.moved', self.handle_new_location)
        self.pubpen.subscribe('ship.info', self.handle_ship_info)
        self.pubpen.subscribe('ship.cargo.update', self.handle_cargo_update)

    #
    # Helpers
    #
    def _highlight_focused_line(self):
        """Highlight the other portions of the commodity line that match with the commodity that's in focus"""
        try:
            idx = self.commodity.focus_position
        except IndexError:
            # The commodity list hasn't been refreshed yet.
            return

        # Reset the auxilliary lists
        for entry in self.price_list:
            entry.set_attr_map({})
        for entry in self.hold_list:
            entry.set_attr_map({})

        # Highlight the appropriate line in each auxilliary list
        self.price_list[idx].set_attr_map({None: 'reversed'})
        self.hold_list[idx].set_attr_map({None: 'reversed'})

    def _sync_commodity_map(self, commodity_map, money=False):
        """
        Make sure the given commodity map contains the same commodities in the
        same order as the main commodity map

        :arg commodity_map: The auxilliary commodity map to check
        :kwarg money: Whether the mapping contains a monetary amount.  This
            influences how zero values are formatted
        """
        new_commodity_map = OrderedDict()
        for commodity in self.commodity_idx_map:
            new_value = commodity_map.get(commodity, None)
            if money:
                if new_value is None:
                    new_value = 0
            else:
                if new_value == 0:
                    new_value = None
            new_commodity_map[commodity] = new_value

        commodity_map = new_commodity_map
        return commodity_map

    def _sync_widget_list(self, widget_list, commodity_map, money=False):
        """
        Make sure the given widget_list contains all the commodities in the correct order

        :arg widget_list: List of widgets that display a specific piece of
            information about the commodity.  For instance, price of the item.
        :arg commodity_map: Ordered mapping of the commodities to the information.
        :kwarg money: Whether the information is a monetary value.  This influences
            the formatting of the information.
        """
        widget_list.clear()
        for commodity, value in commodity_map.items():
            if isinstance(value, int):
                formatted_number = format_number(value)
                if money:
                    button = IndexedMenuButton('${}'.format(formatted_number))
                else:
                    button = IndexedMenuButton('{}'.format(formatted_number))
            else:
                if value is None:
                    value = " "
                button = IndexedMenuButton(value)
            urwid.connect_signal(button, 'click', partial(self.handle_commodity_select, commodity))
            widget_list.append(urwid.AttrMap(button, None))

    def _construct_commodity_list(self, commodities):
        """
        Display the commodities that can be bought and sold

        :arg commodities: iterable of commodity names sold at this market
        """
        for commodity in commodities:
            if commodity not in self.commodity_idx_map:
                idx = self.keypress_map.set_next(commodity)

                button = IndexedMenuButton('({}) {}'.format(idx, commodity))
                self.commodity_list.append(urwid.AttrMap(button, None, focus_map='reversed'))
                urwid.connect_signal(button, 'click', partial(self.handle_commodity_select, commodity))

                self.commodity_idx_map[commodity] = len(self.commodity_list) - 1

        self.commodity_price_map = self._sync_commodity_map(self.commodity_price_map, money=True)
        self.commodity_hold_map = self._sync_commodity_map(self.commodity_hold_map, money=False)

        self._sync_widget_list(self.price_list, self.commodity_price_map, money=True)
        self._sync_widget_list(self.hold_list, self.commodity_hold_map, money=False)


        self._highlight_focused_line()

    #
    # Handle updates to the displayed info
    #
    def handle_market_info(self, prices):
        """
        Update the display with prices about all commodities in a market

        :arg prices: a dict mapping commodity names to prices
        """
        self.pubpen.unsubscribe(self._market_query_sub_id)
        self._market_query_sub_id = None
        for commodity, price in prices.items():
            self.commodity_price_map[commodity] = price
        self._construct_commodity_list(self.commodity_price_map)

    def handle_ship_info(self, ship_type, free_space, filled_space, manifest): #pylint: disable=unused-argument
        """
        Update the display with hold information for all commodities
        """
        for key, value in manifest.items():
            self.commodity_hold_map[key] = value.quantity
        self._construct_commodity_list(self.commodity_hold_map)

    def handle_cargo_update(self, cargo, *args):
        """Update the market display when cargo info changes"""
        self.commodity_hold_map[cargo.commodity] = cargo.quantity
        self._construct_commodity_list(self.commodity_hold_map)

    def handle_new_warehouse_info(self, warehouse_info):
        """Update the market display when warehouse info changes"""
        pass

    def handle_new_location(self, new_location, *args):
        """
        Update the market display when the ship moves

        :arg new_location: The location the ship has moved to
        """
        self.location = new_location
        self.commodity_list.clear()
        self.commodity_idx_map.clear()
        self.keypress_map.clear()
        self.price_list.clear()
        self.commodity_price_map.clear()

        # Sync up information
        if self._market_query_sub_id is None:
            self._market_query_sub_id = self.pubpen.subscribe('market.{}.info'.format(new_location), self.handle_market_info)
        self.pubpen.publish('query.ship.info')

        #self.pubpen.subscribe('market.{}.update'.format(new_location)) => handle new market data
        #self.pubpen.subscribe('warehouse.{}.update'.format(new_location)) => handle new warehouse info
        self.pubpen.publish('query.market.{}.info'.format(new_location))
        self.pubpen.publish('query.warehouse.{}.info'.format(new_location))

    def handle_commodity_select(self, commodity, *args):
        """
        Create a buy/sell dialog when the commodity is selected

        :arg commodity: The name of the commodity selected
        """
        # If the user selected the line via the mouse, then we need to sync
        # the highlighted line
        self.commodity.set_focus(self.commodity_idx_map[commodity])
        self._highlight_focused_line()

        self.pubpen.publish('ui.urwid.order_info', commodity, self.commodity_price_map[commodity], self.location)
        urwid.emit_signal(self, 'open_order_dialog')

    def keypress(self, size, key):
        """Handle all keyboard shortcuts for the market menu"""
        if key in self.keypress_map:
            # Open up the commodity menu to buy sell this item
            pass
            commodity = self.keypress_map[key]
            ### TODO: this should move to when the sale/buy is confirmed
            self.pubpen.publish('ui.urwid.order_info', commodity, self.commodity_price_map[commodity], self.location)
            urwid.emit_signal(self, 'open_order_dialog')
            #urwid.emit_signal(self, 'close_market_display')
        elif key in ('left', 'right'):
            # Ignore keys that might move focus to a widget to the side
            return
        elif key in ('up', 'down', 'page up', 'page down'):
            # First let the children handle the change in focus...
            super().keypress(size, key)  #pylint: disable=not-callable
            # Then highlight the same entry in other columns
            self._highlight_focused_line()
        else:
            super().keypress(size, key)  #pylint: disable=not-callable
        return key

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

import locale
from functools import partial

import urwid

from .indexed_menu import IndexedMenuButton, IndexedMenuEnumerator


class MarketDisplay(urwid.WidgetWrap):
    _selectable = True
    signals = ['close_market_display']

    def __init__(self, pubpen):
        self.pubpen = pubpen
        self.location = None
        self.commodities = []
        self.keypress_map = IndexedMenuEnumerator()
        self.commodity_idx_map = {}

        # Columns
        # LineBox w/ title and custom left/right sides
        # listboxes w/ listwalkers
        # if there's an onselect handler, set that so that we programatically
        # have selection highlight all three column?
        #

        self.commodity_list = urwid.SimpleFocusListWalker([])
        self.price_list = urwid.SimpleFocusListWalker([])
        #self.quantity_list = urwid.SimpleFocusListWalker([])
        self.hold_list = urwid.SimpleFocusListWalker([])
        self.warehouse_list = urwid.SimpleFocusListWalker([])

        self.commodity = urwid.ListBox(self.commodity_list)
        self.price = urwid.ListBox(self.price_list)
        #self.quantity = urwid.ListBox(self.quantity)
        self.hold = urwid.ListBox(self.hold_list)
        self.warehouse = urwid.ListBox(self.warehouse_list)

        market_col = urwid.LineBox(self.commodity, title='Commodity',
                                   trcorner='\u2500', rline=' ',
                                   brcorner='\u2500')
        price_col = urwid.LineBox(self.price, title='Price',
                                  trcorner='\u2500', rline=' ',
                                  brcorner='\u2500', tlcorner='\u2500',
                                  lline=' ', blcorner='\u2500')
        #quantity_col = urwid.LineBox(self.quantity, title='For Sale',
        #                             trcorner='\u2500', rline=' ',
        #                             brcorner='\u2500', tlcorner='\u2500',
        #                             lline=' ', blcorner='\u2500')
        hold_col = urwid.LineBox(self.hold, title='Hold',
                                 trcorner='\u2500', rline=' ',
                                 brcorner='\u2500', tlcorner='\u2500',
                                 lline=' ', blcorner='\u2500')
        warehouse_col = urwid.LineBox(self.warehouse, title='Warehouse',
                                      tlcorner='\u2500', lline=' ',
                                      blcorner='\u2500')

        self.market_display = urwid.Columns([market_col, price_col, hold_col, warehouse_col])

        super().__init__(self.market_display)

        self.pubpen.subscribe('ship.moved', self.handle_new_location)
        #self.pubpen.subscribe('ship.cargo') => handle new cargo information
        #self.pubpen.subscribe('market.update') => handle new market data
        #self.pubpen.subscribe('warehouse.info') => handle new warehouse info

    def handle_button_click(self, commodity, *args):
        # popup the Buy/Sell Window

        ### TODO: this should move to when the sale/buy is confirmed
        urwid.emit_signal(self, 'close_market_display')

    def _construct_commodity_list(self, commodities):
        for commodity in commodities:
            if commodity not in self.commodity_idx_map:
                idx = self.keypress_map.set_next(commodity)

                button = IndexedMenuButton('({}) {}'.format(idx, commodity))
                self.commodity_list.append(urwid.AttrMap(button, None, focus_map='reversed'))
                urwid.connect_signal(button, 'click', partial(self.handle_button_click, commodity))

                self.commodity_idx_map[commodity] = len(self.commodity_list) - 1

    def _construct_price_list(self, prices):
        for commodity, price in prices.items():
            ### FIXME: in the future, might a commodity be added here?
            idx = self.commodity_idx_map[commodity]

            price_formatted = locale.format('%d', price, grouping=True)
            if len(price_formatted) > 7:
                price_formatted = '{:.1E}'.format(number)

            button = IndexedMenuButton('${}'.format(price_formatted))
            self.price_list.append(urwid.AttrMap(button, None))

        self._highlight_focused_commodity_line()

    def _highlight_focused_commodity_line(self):
        idx = self.commodity.focus_position
        for entry in self.price_list:
            entry.set_attr_map({})
        self.price_list[idx].set_attr_map({None: 'reversed'})

    def handle_new_location(self, old_location, new_location):
        self.location = new_location
        self.commodity_list.clear()
        self.commodity_idx_map.clear()
        self.keypress_map.clear()
        self.price_list.clear()
        self.pubpen.publish('query.market.info', new_location)
        self._market_query_id = self.pubpen.subscribe('market.info', self.handle_market_info)
        self.pubpen.publish('query.warehouse.info', new_location)

    def handle_market_info(self, location, prices):
        if location == self.location:
            self.pubpen.unsubscribe(self._market_query_id)
            self._construct_commodity_list(prices.keys())
            self._construct_price_list(prices)

    def handle_cargo_data(self, cargo):
        pass

    def handle_new_warehouse_info(self, warehouse_info):
        pass

    def keypress(self, size, key):
        """Handle all keyboard shortcuts for the travel menu"""
        if key in self.keypress_map:
            # Open up the commodity menu to buy sell this item
            pass
            ### TODO: this should move to when the sale/buy is confirmed
            urwid.emit_signal(self, 'close_market_display')
        elif key in ('left', 'right'):
            # Ignore keys that might move focus to a widget to the side
            return
        elif key in ('up', 'down', 'page up', 'page down'):
            # First let the children handle the change in focus...
            super().keypress(size, key)
            # Then highlight the same entry in other columns
            self._highlight_focused_commodity_line()
        else:
            super().keypress(size, key)
        return key

    def mouse_event(self, *args, **kwargs):
        ### FIXME: Handle button clicks outside of the Commodity list
        super().mouse_event(*args, **kwargs)
        self._highlight_focused_commodity_line()


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

class TransactionDialog(urwid.WidgetWrap):
    """Dialog box to buy or sell a commodity"""
    _selectable = True
    signals = ['close_transaction_dialog']

    def __init__(self, pubpen):
        self.pubpen = pubpen

        self.transaction_type_group = []
        self.buy_button = urwid.RadioButton(self.transaction_type_group, 'Buy')
        self.sell_button = urwid.RadioButton(self.transaction_type_group, 'Sell')
        buysell_widget = urwid.Columns([(len('buy') + 5, self.buy_button), (len('Sell') + 5, self.sell_button)])

        self.hold_box = urwid.CheckBox('Hold:', state=True)

        self.warehouse_box = urwid.CheckBox('Warehouse:', state=True)

        self.sale_info = urwid.Text('Total Sale: $0')

        quantity_label = urwid.Text('Quantity: ')
        self.quantity = urwid.IntEdit()
        self.max_button = urwid.Button('MAX')
        quantity_widget = urwid.Columns([(len('Quantity: '), quantity_label), self.quantity, (len('MAX') + 4, self.max_button)])

        self.commit_button = urwid.Button('Make Transaction')
        commit_widget = urwid.Columns([urwid.Text(''), (len('Make Transaction') + 4, self.commit_button)])

        outer_layout_list = urwid.SimpleFocusListWalker([buysell_widget, self.hold_box, self.warehouse_box, self.sale_info, quantity_widget, commit_widget])
        outer_layout = urwid.ListBox(outer_layout_list)

        self.dialog = urwid.LineBox(outer_layout, tlcorner='\u2554',
                                    tline='\u2550', trcorner='\u2557',
                                    blcorner='\u255A', bline='\u2550',
                                    brcorner='\u255D', lline='\u2551',
                                    rline='\u2551')

        padding = urwid.Padding(self.dialog, align='center',
                width=len('Quantity: ') + len('MAX') + 4 + 20)
        filler = urwid.Filler(padding, valign='middle',
                              height=len(outer_layout_list) + 2)

        super().__init__(filler)

        self.pubpen.subscribe('ui.urwid.sale_info', self.handle_new_sale)

    def handle_new_sale(self, commodity, price):
        """Reset the dialog box whenever a new sale is started

        :arg commodity: The commodity that is being bought or sold
        :arg price: The amount that the commodity is selling for
        """
        self.dialog.set_title('{} - ${}'.format(commodity, price))
        pass
        # reset radio buttons to buy
        # reset checkboxes for hold and warehouse
        # recalculate hold and warehouse space
        # reset quantity to 0

    def handle_buy_sell_toggle(self):
        """Change interface slightly depending on whether we're buying or selling"""
        pass

    def handle_max_quantity(self):
        """Calculate the maximum quantity to buy or sell"""
        pass

    def handle_make_transaction(self):
        """Request to make the transaction"""
        pass


class MarketDisplay(urwid.WidgetWrap):
    """Display the market information to buy and sell commodities"""
    _selectable = True
    signals = ['close_market_display', 'open_transaction_dialog']

    def __init__(self, pubpen):
        self.pubpen = pubpen
        self.location = None
        self.commodities = []
        self.keypress_map = IndexedMenuEnumerator()
        self.commodity_idx_map = {}
        self.commodity_price_map = {}
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

        market_col = urwid.LineBox(self.commodity, title='Commodity',
                                   trcorner='\u2500', rline=' ',
                                   brcorner='\u2500')
        price_col = urwid.LineBox(self.price, title='Price',
                                  trcorner='\u2500', rline=' ',
                                  brcorner='\u2500', tlcorner='\u2500',
                                  lline=' ', blcorner='\u2500')
        #amount_col = urwid.LineBox(self.amount, title='For Sale',
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

    # Populate the columns of the Market Display

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
                urwid.connect_signal(button, 'click', partial(self.handle_button_click, commodity))

                self.commodity_idx_map[commodity] = len(self.commodity_list) - 1

    def _construct_price_list(self, prices):
        """
        Display the prices for commoditites

        :arg prices: Dict that maps commodity names to prices
        """
        for commodity, price in prices.items():
            idx = self.commodity_idx_map[commodity]

            price_formatted = locale.format('%d', price, grouping=True)
            if len(price_formatted) > 7:
                price_formatted = '{:.1E}'.format(number)

            button = IndexedMenuButton('${}'.format(price_formatted))
            self.price_list.append(urwid.AttrMap(button, None))

        self._highlight_focused_commodity_line()

    def _construct_hold_list(self, amounts):
        """
        Display the amount of a commodity in the ship's hold

        :arg amounts: Dictionary mapping commodity names to the amount stored
            on the ship.
        """
        for commodity, amount in amounts.items():
            idx = self.commodity_idx_map[commodity]

            amount_formatted = locale.format('%d', amount, grouping=True)
            if len(amount_formatted) > 7:
                amount_formatted = '{:.1E}'.format(number)

            button = IndexedMenuButton('${}'.format(amount_formatted))
            self.hold_list.append(urwid.AttrMap(button, None))

        self._highlight_focused_commodity_line()

    def handle_button_click(self, commodity, *args):
        # popup the Buy/Sell Window

        self.pubpen.publish('ui.urwid.sale_info', commodity, self.commodity_price_map[commodity])
        urwid.emit_signal(self, 'open_transaction_dialog')
        ### TODO: this should move to when the sale/buy is confirmed
        #urwid.emit_signal(self, 'close_market_display')

    def _highlight_focused_commodity_line(self):
        try:
            idx = self.commodity.focus_position
        except IndexError:
            # The commodity list hasn't been refreshed yet.
            idx = 0
        for entry in self.price_list:
            entry.set_attr_map({})
        self.price_list[idx].set_attr_map({None: 'reversed'})

    def handle_new_location(self, new_location, old_location):
        self.location = new_location
        self.commodity_list.clear()
        self.commodity_idx_map.clear()
        self.keypress_map.clear()
        self.price_list.clear()
        self.commodity_price_map.clear()

        #self.pubpen.subscribe('market.{}.update'.format(new_location)) => handle new market data
        #self.pubpen.subscribe('warehouse.{}.update'.format(new_location)) => handle new warehouse info
        if self._market_query_sub_id is None:
            self._market_query_sub_id = self.pubpen.subscribe('market.{}.info'.format(new_location), self.handle_market_info)
        self.pubpen.publish('query.market.{}.info'.format(new_location))
        self.pubpen.publish('query.warehouse.{}.info'.format(new_location))

    def handle_market_info(self, prices):
        self.pubpen.unsubscribe(self._market_query_sub_id)
        self._market_query_sub_id = None
        self._construct_commodity_list(prices.keys())
        self._construct_price_list(prices)
        self.commodity_price_map = prices

    def handle_cargo_data(self, cargo):
        pass

    def handle_new_warehouse_info(self, warehouse_info):
        pass

    def keypress(self, size, key):
        """Handle all keyboard shortcuts for the travel menu"""
        if key in self.keypress_map:
            # Open up the commodity menu to buy sell this item
            pass
            commodity = self.keypress_map[key]
            ### TODO: this should move to when the sale/buy is confirmed
            self.pubpen.publish('ui.urwid.sale_info', commodity, self.commodity_price_map[commodity])
            urwid.emit_signal(self, 'open_transaction_dialog')
            #urwid.emit_signal(self, 'close_market_display')
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
        ### FIXME: !!! Set commodity to the commodity that was clicked on
        self.pubpen.publish('ui.urwid.sale_info', commodity, self.commodity_price_map[commodity])
        urwid.emit_signal(self, 'open_transaction_dialog')

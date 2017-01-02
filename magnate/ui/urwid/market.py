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
""" Handle the display of Markets and Commodities"""

from functools import partial

import urwid

from ..event_api import Order
from .indexed_menu import IndexedMenuButton, IndexedMenuEnumerator
from .numbers import format_number
from .sideless_linebox import SidelessLineBox


class TransactionDialog(urwid.WidgetWrap):
    """Dialog box to buy or sell a commodity"""
    _selectable = True
    signals = ['close_transaction_dialog']

    def __init__(self, pubpen):
        self.pubpen = pubpen
        self.order = None
        self._order_purchased_sub_id = None
        self._order_sold_sub_id = None

        transaction_type_group = []
        self.buy_button = urwid.RadioButton(transaction_type_group, 'Buy')
        self.sell_button = urwid.RadioButton(transaction_type_group, 'Sell')
        self.buysell_widget = urwid.Columns([(len('buy') + 5, self.buy_button), (len('Sell') + 5, self.sell_button)])

        self.hold_box = urwid.CheckBox('Hold:', state=True)

        self.warehouse_box = urwid.CheckBox('Warehouse:', state=True)

        self.sale_info = urwid.Text('Total Sale: $0')

        quantity_label = urwid.Text('Quantity: ')
        self.quantity = urwid.IntEdit()
        self.max_button = urwid.Button('MAX')
        quantity_widget = urwid.Columns([(len('Quantity: '), quantity_label), self.quantity, (len('MAX') + 4, self.max_button)])

        self.commit_button = urwid.Button('Place Order')
        self.cancel_button = urwid.Button('Cancel')
        commit_widget = urwid.Columns([urwid.Text(''), (len('Place Order') + 4, self.commit_button), (len('Cancel') + 4, self.cancel_button)])

        self.layout_list = urwid.SimpleFocusListWalker([self.buysell_widget, self.hold_box,
                                                        self.warehouse_box, self.sale_info,
                                                        quantity_widget, commit_widget])
        layout = urwid.ListBox(self.layout_list)

        self.dialog = urwid.LineBox(layout, tlcorner='\u2554',
                                    tline='\u2550', trcorner='\u2557',
                                    blcorner='\u255A', bline='\u2550',
                                    brcorner='\u255D', lline='\u2551',
                                    rline='\u2551')

        padding = urwid.Padding(self.dialog, align='center',
                                width=max(len('Quantity: ') + len('MAX') + 4 + 20,
                                          len('Place Order') + len('Cancel') + 8))
        filler = urwid.Filler(padding, valign='middle',
                              height=len(self.layout_list) + 2)

        outer_layout = SidelessLineBox(filler, lline=None, tlcorner='─',
                                       blcorner='─', trcorner='\u252c',
                                       brcorner='\u2524')
        super().__init__(outer_layout)

        urwid.connect_signal(self.commit_button, 'click', self.handle_place_order)
        urwid.connect_signal(self.cancel_button, 'click', self.handle_transaction_finalized)
        self.pubpen.subscribe('ui.urwid.order_info', self.create_new_transaction)

    def create_new_transaction(self, commodity, price, location):
        """Reset the dialog box whenever a new sale is started

        :arg commodity: The commodity that is being bought or sold
        :arg price: The amount that the commodity is selling for
        :arg location: The location the transaction is taking place
        """
        self.order = Order(location, commodity, price)
        self.dialog.set_title('{} - ${}'.format(commodity, price))

        # Reset the form elements
        self.buy_button.set_state(True, do_callback=False)
        self.hold_box.set_state(True, do_callback=False)
        self.warehouse_box.set_state(True, do_callback=False)
        self.sale_info.set_text('Total Sale: $0')
        self.quantity.set_edit_text("")
        self.buysell_widget.focus_position = 0
        self.layout_list.set_focus(0)
        pass
        # recalculate hold and warehouse space

    def handle_buy_sell_toggle(self):
        """Change interface slightly depending on whether we're buying or selling"""
        pass
        # If buy sell changed, then change hold and warehouse numbers
        # (free space for buy, amount of item for sell)
        # If quantity exceeds maximum, reduce it to the maximum

    def handle_max_quantity(self):
        """Calculate the maximum quantity to buy or sell"""
        pass
        # For buy, if hold is checked use hold_space for maximum_space
        #       if warehouse, add that to the maximum_space
        #   calculate maximum amount to buy for user's money.
        #   if amount to buy > maximum_space, reduce to maximum_space
        #   set quantity field to maximum_space
        #   set total_sale to quantity * price
        #
        # For sell, if hold is checked, set amount_to_sell to hold
        #       if warehouse, add to amount_to_sell
        #   set quantity field to amount_to_sell
        #   set total_sale to quantity field * price

    def validate_check_box_change(self):
        """Make sure that at least one of the hold/warehouse checkboxes is always checked"""
        pass

    def handle_transaction_finalized(self, *args, **kwargs):
        """
        Clear the transation dialog state when we are told the transaction is finished.

        This cleans up the event notifications and closes the dialog.
        """
        if self._order_sold_sub_id:
            self.pubpen.unsubscribe(self._order_sold_sub_id)
            self._order_sold_sub_id = None
        if self._order_purchased_sub_id:
            self.pubpen.unsubscribe(self._order_purchased_sub_id)
            self._order_purchased_sub_id = None

        urwid.emit_signal(self, 'close_transaction_dialog')

    def handle_place_order(self, *args):
        """Request to make the transaction"""
        if self.buy_button.state is True:
            self.order.buy = True
            if self.hold_box.get_state() is True:
                ### TODO: place the min() of quantity or hold free space here.
                # put rest in warehouse
                self.order.hold_quantity = self.quantity.value()
            if self.warehouse_box.get_state() is True:
                ### TODO: implement warehouse
                pass
            ### TODO: if there's still more quantity, error?  (or reduce)
            if self._order_purchased_sub_id is None:
                self._order_purchased_sub_id = self.pubpen.subscribe('market.{}.purchased'.format(self.order.location),
                                                                     self.handle_transaction_finalized)
            self.pubpen.publish('action.user.order', self.order)
        elif self.sell_button.state is True:
            self.order.buy = False
            if self.hold_box.get_state() is True:
                ### TODO: place the min() of quantity or amount of commodity in hold
                # take rest from warehouse
                self.order.hold_quantity = self.quantity.value()
            if self.warehouse_box.get_state() is True:
                ### TODO: implement warehouse
                pass
            if self._order_sold_sub_id is None:
                self._order_sold_sub_id = self.pubpen.subscribe('market.{}.sold'.format(self.order.location),
                                                                self.handle_transaction_finalized)
            self.pubpen.publish('action.user.order', self.order)
            pass
        else:
            # Error
            assert self.buy_button.state is True or self.sell_button.state is True, 'Neither the buy nor sell button was selected'

    def keypress(self, size, key):
        """Handle all keyboard shortcuts for the transaction dialog"""
        if key == 'esc':
            self.handle_transaction_finalized()
        elif key == 'enter':
            self.handle_place_order()
        else:
            super().keypress(size, key)  #pylint: disable=not-callable
        return key


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
        hold_col = SidelessLineBox(self.hold, title='Hold',
                                   trcorner='\u2500', rline=None,
                                   brcorner='\u2500', tlcorner='\u2500',
                                   lline=None, blcorner='\u2500')
        warehouse_col = SidelessLineBox(self.warehouse, title='Warehouse',
                                        tlcorner='\u2500', lline=None, blcorner='\u2500',
                                        trcorner='\u252c', brcorner='\u2524')

        self.market_display = urwid.Columns([('weight', 2, market_col), (13, price_col), (20, hold_col), (20, warehouse_col)])

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
                urwid.connect_signal(button, 'click', partial(self.handle_commodity_select, commodity))

                self.commodity_idx_map[commodity] = len(self.commodity_list) - 1

    def _construct_price_list(self, prices):
        """
        Display the prices for commoditites

        :arg prices: Dict that maps commodity names to prices
        """
        for commodity, price in prices.items():
            formatted_price = format_number(price)

            button = IndexedMenuButton('${}'.format(formatted_price))
            self.price_list.append(urwid.AttrMap(button, None))

        self._highlight_focused_commodity_line()

    def _construct_hold_list(self, amounts):
        """
        Display the amount of a commodity in the ship's hold

        :arg amounts: Dictionary mapping commodity names to the amount stored
            on the ship.
        """
        for commodity, amount in amounts.items():
            formatted_amount = format_number(amount)

            button = IndexedMenuButton('${}'.format(formatted_amount))
            self.hold_list.append(urwid.AttrMap(button, None))

        self._highlight_focused_commodity_line()

    def handle_commodity_select(self, commodity, *args):
        """
        Create a buy/sell dialog when the commodity is selected

        :arg commodity: The name of the commodity selected
        """
        self.pubpen.publish('ui.urwid.order_info', commodity, self.commodity_price_map[commodity], self.location)
        urwid.emit_signal(self, 'open_transaction_dialog')

    def _highlight_focused_commodity_line(self):
        """Highlight the other portions of the commodity line that match with the commodity that's in focus"""
        try:
            idx = self.commodity.focus_position
        except IndexError:
            # The commodity list hasn't been refreshed yet.
            idx = 0
        for entry in self.price_list:
            entry.set_attr_map({})
        self.price_list[idx].set_attr_map({None: 'reversed'})

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

        #self.pubpen.subscribe('market.{}.update'.format(new_location)) => handle new market data
        #self.pubpen.subscribe('warehouse.{}.update'.format(new_location)) => handle new warehouse info
        if self._market_query_sub_id is None:
            self._market_query_sub_id = self.pubpen.subscribe('market.{}.info'.format(new_location), self.handle_market_info)
        self.pubpen.publish('query.market.{}.info'.format(new_location))
        self.pubpen.publish('query.warehouse.{}.info'.format(new_location))

    def handle_market_info(self, prices):
        """
        Update the display with prices about all commodities in a market

        :arg prices: a dict mapping commodity names to prices
        """
        self.pubpen.unsubscribe(self._market_query_sub_id)
        self._market_query_sub_id = None
        self._construct_commodity_list(prices.keys())
        self._construct_price_list(prices)
        self.commodity_price_map = prices

    def handle_cargo_data(self, cargo):
        """Update the market display when cargo info changes"""
        pass

    def handle_new_warehouse_info(self, warehouse_info):
        """Update the market display when warehouse info changes"""
        pass

    def keypress(self, size, key):
        """Handle all keyboard shortcuts for the market menu"""
        if key in self.keypress_map:
            # Open up the commodity menu to buy sell this item
            pass
            commodity = self.keypress_map[key]
            ### TODO: this should move to when the sale/buy is confirmed
            self.pubpen.publish('ui.urwid.order_info', commodity, self.commodity_price_map[commodity], self.location)
            urwid.emit_signal(self, 'open_transaction_dialog')
            #urwid.emit_signal(self, 'close_market_display')
        elif key in ('left', 'right'):
            # Ignore keys that might move focus to a widget to the side
            return
        elif key in ('up', 'down', 'page up', 'page down'):
            # First let the children handle the change in focus...
            super().keypress(size, key)  #pylint: disable=not-callable
            # Then highlight the same entry in other columns
            self._highlight_focused_commodity_line()
        else:
            super().keypress(size, key)  #pylint: disable=not-callable
        return key

    def mouse_event(self, *args, **kwargs):
        """Handle all mouse clicks for the market menu"""
        ### FIXME: Handle button clicks outside of the Commodity list
        super().mouse_event(*args, **kwargs)  #pylint: disable=not-callable
        self._highlight_focused_commodity_line()
        ### FIXME: !!! Set commodity to the commodity that was clicked on
        self.pubpen.publish('ui.urwid.order_info', commodity, self.commodity_price_map[commodity], self.location)
        urwid.emit_signal(self, 'open_transaction_dialog')

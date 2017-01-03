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
        self._market_update_sub_id = None
        self._user_info_sub_id = None

        self.free_space = 0
        self.commodity_in_hold = 0
        self.free_warehouse = 0
        self.commodity_in_warehouse = 0
        self.user_cash = None

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

        urwid.connect_signal(self.buy_button, 'change', self.handle_buy_sell_toggle)
        urwid.connect_signal(self.quantity, 'change', self.handle_quantity_change)
        urwid.connect_signal(self.commit_button, 'click', self.handle_place_order)
        urwid.connect_signal(self.cancel_button, 'click', self.handle_transaction_finalized)
        urwid.connect_signal(self.max_button, 'click', self.handle_max_quantity)

        self.pubpen.subscribe('ui.urwid.order_info', self.create_new_transaction)
        self.pubpen.subscribe('user.cash.update', self.handle_user_cash_update)
        self.pubpen.subscribe('ship.info', self.handle_ship_info)
        self.pubpen.subscribe('ship.cargo.update', self.handle_cargo_update)
        #self.pubpen.subscribe('warehouse.{}.info', self.handle_warehouse_info)
        #self.pubpen.subscribe('warehouse.{}.cargo.update', self.handle_cargo_update)

    #
    # Urwid event handlers for the dialog box elements
    #
    def handle_buy_sell_toggle(self, radio_button, new_state):
        """Change interface slightly depending on whether we're buying or selling"""
        ### FIXME: Implement warehouse
        if (radio_button is self.buy_button and new_state is True) or (radio_button is self.sell_button and new_state is False):
            self.hold_box.set_label('Hold: {} Free Space'.format(format_number(self.free_space)))
            #self.warehouse_box.set_label('Warehouse: {}'.format(format_number(self.free_warehouse)))
        else:
            self.hold_box.set_label('Hold: {} {}'.format(format_number(self.commodity_in_hold),
                                                         self.order.commodity))
            #self.warehouse_box.set_label('Warehouse: {}'.format(format_number(self.commodity_in_warehouse)))
        ###FIXME: If quantity exceeds maximum, reduce it to the maximum

    def handle_quantity_change(self, edit_widget, new_text):
        """Update total sale as the edit widget is changed"""
        try:
            quantity = int(new_text)
        except ValueError:
            # EditInt's change signal also fires when the widget is first
            # created or cleared (and thus has empty string or other
            # non-numbers)
            return
        total_sale = quantity * self.order.price
        self.sale_info.set_text('Total Sale: ${}'.format(format_number(total_sale)))

    def handle_max_quantity(self, *args):
        """Calculate the maximum quantity to buy or sell"""

        if self.buy_button.state:
            # Find out how much space we have available in the hold and local
            # warehouse
            available_space = 0
            if self.hold_box.state:
                available_space += self.free_space
            if self.warehouse_box.state:
                available_space += self.free_warehouse

            # maximum amount we can buy is the smaller of space available or cash/price
            maximum_quantity = min(available_space, self.user_cash // self.order.price)
            total_sale = self.order.price * maximum_quantity

            # set quantity field to maximum_quantity
            self.quantity.set_edit_text('{}'.format(maximum_quantity))
            # Set the total_sale information to the amount we'd pay for the
            # maximum
            self.sale_info.set_text('Total Sale: ${}'.format(format_number(total_sale)))
        else:
            # Find how much of the commodity we have to sell
            amount = 0
            if self.hold_box.state:
                amount += self.commodity_in_hold
            if self.warehouse_box.state:
                amount += self.commodity_in_warehouse

            # Set the quantity and total sale fields to reflect this amount
            self.quantity.set_edit_text('{}'.format(amount))
            self.sale_info.set_text('Total Sale: ${}'.format(format_number(amount * self.order.price)))

    def validate_check_box_change(self):
        """Make sure that at least one of the hold/warehouse checkboxes is always checked"""
        pass

    #
    # Event handlers for processing the transaction
    #
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

        # recalculate hold and warehouse space
        self.pubpen.publish('query.ship.info')
        ### FIXME: Recalculate warehouse space
        pass

        # Watch out for price changes
        if self._market_update_sub_id:
            self.pubpen.unsubscribe(self._market_update_sub_id)
        self._market_update_sub_id = self.pubpen.subscribe('market.{}.update'.format(location),
                                                           self.handle_market_update)

        # If we haven't acquired information about the user's cash yet, query
        # once for it.  After the initial time, the user.cash.update event
        # should keep us informed
        if self.user_cash is None:
            if not self._user_info_sub_id:
                self._user_info_sub_id = self.pubpen.subscribe('user.info', self.handle_user_info)
            self.pubpen.publish('query.user.info')

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
        if self._market_update_sub_id:
            self.pubpen.unsubscribe(self._market_update_sub_id)
            self._market_update_sub_id = None

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

    #
    # Pubpen events to gather data
    #
    def handle_user_info(self, username, cash, *args):
        """Update the user's cash amount"""
        if self._user_info_sub_id:
            self.pubpen.unsubscribe(self._user_info_sub_id)
            self._user_info_sub_id = None
        self.user_cash = cash
        ### FIXME: should we error or reduce quantity?

    def handle_user_cash_update(self, new_cash, *args):
        """Update the user's cash amount"""
        self.user_cash = new_cash
        ### FIXME: should we error or reduce quantity?

    def handle_ship_info(self, ship_type, free_space, filled_space, manifest):
        """Update the hold space """
        self.free_space = free_space
        if self.order is not None:
            commodity = self.order.commodity
            manifest_entry = manifest.get(commodity, None)
            self.commodity_in_hold = manifest_entry.quantity if manifest_entry else 0
        else:
            commodity = ''

        if self.buy_button.state is True:
            self.hold_box.set_label('Hold: {} Free Space'.format(format_number(self.free_space)))
        else:
            self.hold_box.set_label('Hold: {} {}'.format(format_number(self.commodity_in_hold),
                                                         commodity))
    def handle_cargo_update(self, manifest, free_space, *args):
        """Update the hold space whenever we receive a cargo update event"""
        self.free_space = free_space
        if self.order is not None:
            commodity = self.order.commodity
            if manifest.commodity == commodity:
                self.commodity_in_hold = manifest.quantity
        else:
            commodity = ''

        if self.buy_button.state is True:
            self.hold_box.set_label('Hold: {} Free Space'.format(format_number(self.free_space)))
        else:
            self.hold_box.set_label('Hold: {} {}'.format(format_number(self.commodity_in_hold),
                                                         commodity))

    def handle_market_update(self, commodity, price):
        """Update the price in the dialog if it's been updated on the backend"""
        if self.order is not None:
            if commodity == self.order.commodity:
                self.order.price = price
            self.dialog.set_title('{} - ${}'.format(commodity, price))

    def keypress(self, size, key):
        """Handle all keyboard shortcuts for the transaction dialog"""
        if key == 'esc':
            self.handle_transaction_finalized()
        #elif key == 'enter':
        #    self.handle_place_order()
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
        urwid.emit_signal(self, 'open_transaction_dialog')

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
            self._highlight_focused_line()
        else:
            super().keypress(size, key)  #pylint: disable=not-callable
        return key

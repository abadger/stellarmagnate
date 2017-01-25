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
""" Handle the display of a dialog to purchase commodities"""

from abc import abstractmethod

import urwid

from ...order import Order
from .abcwidget import ABCWidget
from .message_win import MsgType
from .numbers import format_number
from .urwid_fixes import LineBox, IntEdit, RadioButton

class OrderDialog(urwid.WidgetWrap, metaclass=ABCWidget):
    """Dialog box to buy or sell a commodity"""
    _selectable = True
    """
    Must have a signals attribute that is a list containing at least one urwid
    signal name.

    (1) Signal to close the OrderDialog

    This signal is referenced by offset so it's important to keep it as the
    first signal in the list.  Other signals may be added as long as they are
    mentioned afterwards.

    The _sub_ids instance attribute is a dict used to track subscriptions to
    the event system.  Implementations should add any sub_ids here that are
    transient in nature (for instance, those that are location based).  The
    _sub_ids are cleared after a transaction is processed and the dialog is
    closed.
    """
    signals = []

    def __init__(self, pubpen, extra_widgets=tuple()):
        """
        Order form for purchasing commodities

        :arg pubpen: Pubpen for events
        :kwarg extra_widgets: Sequence of widgets that display some more
            information about the Order.
        """
        self.pubpen = pubpen
        self.order = None
        self._sub_ids = {}

        self.user_cash = None

        self.extra_widgets = extra_widgets

        self.sale_info = urwid.Text('Total Sale: $0')

        transaction_type_group = []
        self.buy_button = RadioButton(transaction_type_group, 'Buy')
        self.sell_button = RadioButton(transaction_type_group, 'Sell')
        self.buysell_widget = urwid.Columns([(len('buy') + 5, self.buy_button), (len('Sell') + 5, self.sell_button)])

        quantity_label = urwid.Text(' Quantity: ')
        self.max_button = urwid.Button('MAX')
        self.quantity = IntEdit()
        quantity_widget = urwid.Columns([(len('MAX') + 4, self.max_button),
                                         (len(' Quantity: '), quantity_label),
                                         self.quantity])

        self.commit_button = urwid.Button('Place Order')
        self.cancel_button = urwid.Button('Cancel')
        commit_widget = urwid.Columns([urwid.Text(''),
                                       (len('Place Order') + 4, self.commit_button),
                                       (len('Cancel') + 4, self.cancel_button)])

        widgets = [self.sale_info, self.buysell_widget]
        widgets.extend(self.extra_widgets)
        widgets.extend((quantity_widget, commit_widget))
        self.layout_list = urwid.SimpleFocusListWalker(widgets)
        layout = urwid.ListBox(self.layout_list)

        self.dialog = urwid.LineBox(layout, tlcorner='\u2554',
                                    tline='\u2550', trcorner='\u2557',
                                    blcorner='\u255A', bline='\u2550',
                                    brcorner='\u255D', lline='\u2551',
                                    rline='\u2551')

        padding = urwid.Padding(self.dialog, align='center',
                                width=max(len(' Quantity: ') + len('MAX') + 4 + 20,
                                          len('Place Order') + len('Cancel') + 8))
        filler = urwid.Filler(padding, valign='middle',
                              height=len(self.layout_list) + 2)

        outer_layout = LineBox(filler, lline=None, tlcorner='─',
                                       blcorner='─', trcorner='\u252c',
                                       brcorner='\u2524')
        super().__init__(outer_layout)

        urwid.connect_signal(self.buy_button, 'postchange', self.handle_buy_sell_toggle)
        urwid.connect_signal(self.quantity, 'postchange', self.handle_quantity_change)
        urwid.connect_signal(self.commit_button, 'click', self.handle_place_order)
        urwid.connect_signal(self.cancel_button, 'click', self.handle_transaction_finalized)
        urwid.connect_signal(self.max_button, 'click', self.handle_max_quantity)

        self.pubpen.subscribe('ui.urwid.order_info', self.create_new_transaction)
        self.pubpen.subscribe('user.cash.update', self.handle_user_cash_update)

    #
    # Urwid event handlers for the dialog box elements
    #
    @property
    @abstractmethod
    def max_buy_quantity(self):
        """
        Maximum amount of a commodity that may be bought and not be invalid

        Implementations override this to add additional constraints on how
        much can be bought.
        """
        if self.user_cash and self.order.price:
            return self.user_cash // self.order.price
        else:
            return 0

    @property
    @abstractmethod
    def max_sell_quantity(self):
        """
        Maximum amount of a commodity that may be sold and not be invalid

        Implementations override this to add additional constraints on how
        much can be sold.
        """
        return 0

    def validate_quantity(self, revert_amount=None):
        valid = True
        quantity = self.quantity.value()

        if self.buy_button.state:
            if quantity > self.max_buy_quantity:
                valid = False
                if revert_amount is None:
                    quantity = self.max_buy_quantity
                else:
                    quantity = revert_amount
                self.quantity.set_edit_text('{}'.format(quantity))
        else:
            if quantity > self.max_sell_quantity:
                valid = False
                if revert_amount is None:
                    quantity = self.max_sell_quantity
                else:
                    quantity = revert_amount
                self.quantity.set_edit_text('{}'.format(quantity))

        total_sale = quantity * self.order.price
        self.sale_info.set_text('Total Sale: ${}'.format(format_number(total_sale)))
        return valid

    def handle_quantity_change(self, edit_widget, old_text):
        """Update total sale as the edit widget is changed"""
        if not old_text:
            old_text = 0
        was_valid = self.validate_quantity(revert_amount=int(old_text))

        if not was_valid:
            if self.buy_button.state:
                msg_args = ('buy', self.max_buy_quantity, self.order.commodity)
            else:
                msg_args = ('sell', self.max_sell_quantity, self.order.commodity)

            self.pubpen.publish('ui.urwid.message',
                                'Cannot {} more than {} {} at this time'.format(*msg_args),
                                severity=MsgType.error)

    def handle_buy_sell_toggle(self, radio_button, new_state):
        """
        Handle the buy sell toggle being changed

        :arg radio_button: The button being changes
        :arg new_state: Whether the button is selected or unselected

        The base handles making sure that the quantity in the order does not
        exceed the maximum that can be bought and sold.  Implementations may
        want to override this to add other changes on state change
        """
        self.validate_quantity()

    def handle_max_quantity(self, *args):
        """Calculate the maximum quantity to buy or sell"""

        if self.buy_button.state:
            # set quantity field to maximum_quantity
            self.quantity.set_edit_text('{}'.format(self.max_buy_quantity))
            # Set the total_sale information to the amount we'd pay for the
            # maximum
            total_sale = self.order.price * self.max_buy_quantity
            self.sale_info.set_text('Total Sale: ${}'.format(format_number(total_sale)))
        else:
            # Set the quantity and total sale fields to the maximum we # can sell
            self.quantity.set_edit_text('{}'.format(self.max_sell_quantity))
            total_sale = self.order.price * self.max_sell_quantity
            self.sale_info.set_text('Total Sale: ${}'.format(format_number(total_sale)))

    def finalize(self):
        """
        This cleans up the event notifications that the dialog is subscribed to.

        This method is appropriate for both internal and external callers to use
        when they close the dialog.

        Implementations should extend this if they have any cleanup to perform.
        """
        for sub_id in self._sub_ids.values():
            self.pubpen.unsubscribe(sub_id)
        self._sub_ids.clear()

    #
    # Event handlers for processing the transaction
    #
    def create_new_transaction(self, commodity, price, location):
        """Reset the dialog box whenever a new sale is started

        :arg commodity: The commodity that is being bought or sold
        :arg price: The amount that the commodity is selling for
        :arg location: The location the transaction is taking place

        Implementations extend this in order to reset their extra_widgets
        """
        self.order = Order(location, commodity, price)
        self.dialog.set_title('{} - ${}'.format(commodity, price))

        # Reset the form elements
        self.buy_button.set_state(True, do_callback=False)
        self.sale_info.set_text('Total Sale: $0')
        self.quantity.set_edit_text('0')
        self.quantity.edit_pos = 1
        self.buysell_widget.focus_position = 0
        self.layout_list.set_focus(1)

        # Watch out for price changes
        if 'market' in self._sub_ids:
            self.pubpen.unsubscribe(self._sub_ids['market'])
        self._sub_ids['market'] = self.pubpen.subscribe('market.{}.update'.format(location),
                                                                  self.handle_market_update)

        # If we haven't acquired information about the user's cash yet, query
        # once for it.  After the initial time, the user.cash.update event
        # should keep us informed
        if self.user_cash is None:
            if 'user_info' not in self._sub_ids:
                self._sub_ids['user_info'] = self.pubpen.subscribe('user.info', self.handle_user_info)
            self.pubpen.publish('query.user.info')

    def handle_transaction_finalized(self, *args, **kwargs):
        """
        Clear the transation dialog state when we are told the transaction is finished.

        This cleans up the event notifications and closes the dialog.
        """
        self.finalize()

        # Close the dialog
        urwid.emit_signal(self, self.signals[0])

    #@abstractmethod
    def handle_place_order(self, *args):
        """
        Request to make the transaction

        This method assembles a :class:`magnate.order.Order` and sends it to
        the backend to request that it be finalized.

        Implementors of this method should make the call to the backend as the
        last thing they do like this::
            self.pubpen.publish('action.user.order', self.order)

        This base method takes care of listening for the success or failure messages.
        """
        if self.buy_button.state is True:
            self.order.buy = True
            if 'order_purchased' not in self._sub_ids:
                self._sub_ids['order_purchased'] = self.pubpen.subscribe('market.{}.purchased'.format(self.order.location),
                                                                         self.handle_transaction_finalized)
        elif self.sell_button.state is True:
            self.order.buy = False
            if 'order_sold' not in self._sub_ids:
                self._sub_ids['order_sold'] = self.pubpen.subscribe('market.{}.sold'.format(self.order.location),
                                                                    self.handle_transaction_finalized)
        else:
            # Error
            assert self.buy_button.state is True or self.sell_button.state is True, 'Neither the buy nor sell button was selected'

    #
    # Pubpen events to gather data
    #
    def handle_user_info(self, username, cash, *args):
        """Update the user's cash amount"""
        if 'user_info' in self._sub_ids:
            self.pubpen.unsubscribe(self._sub_ids['user_info'])
            del self._sub_ids['user_info']
        self.user_cash = cash

        self.validate_quantity()

    def handle_user_cash_update(self, new_cash, *args):
        """Update the user's cash amount"""
        self.user_cash = new_cash
        self.validate_quantity()

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

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
from .numbers import format_number
from .urwid_fixes import LineBox, IntEdit, CheckBox, RadioButton

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

    def validate_quantity(self):
        quantity = self.quantity.value()

        if self.buy_button.state:
            if quantity > self.max_buy_quantity:
                ### TODO: better to highlight this as an error than to change it
                # That way a user who just gets one digit wrong can edit it
                quantity = self.max_buy_quantity
                self.quantity.set_edit_text('{}'.format(quantity))
        else:
            if quantity > self.max_sell_quantity:
                ### TODO: better to highlight this as an error than to change it
                # That way a user who just gets one digit wrong can edit it
                quantity = self.max_sell_quantity
                self.quantity.set_edit_text('{}'.format(quantity))
            pass

        total_sale = quantity * self.order.price
        self.sale_info.set_text('Total Sale: ${}'.format(format_number(total_sale)))

    def handle_quantity_change(self, edit_widget, old_text):
        """Update total sale as the edit widget is changed"""
        self.validate_quantity()

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
        if 'market_update' in self._sub_ids:
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

    #@abstractmethod
    def handle_transaction_finalized(self, *args, **kwargs):
        """
        Clear the transation dialog state when we are told the transaction is finished.

        This cleans up the event notifications and closes the dialog.

        Implementations should extend this to cleanup any event listeners that
        they may have added.
        """
        for sub_id in self._sub_ids.values():
            self.pubpen.unsubscribe(sub_id)
        self._sub_ids.clear()

        # Close the dialog
        urwid.emit_signal(self, self.signals[0])

    #@abstractmethod
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
            if 'order_purchased' not in self._sub_ids:
                self._sub_ids['order_purchased'] = self.pubpen.subscribe('market.{}.purchased'.format(self.order.location),
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
            if 'order_sold' not in self._sub_ids:
                self._sub_ids['order_sold'] = self.pubpen.subscribe('market.{}.sold'.format(self.order.location),
                                                                              self.handle_transaction_finalized)
            self.pubpen.publish('action.user.order', self.order)
            pass
        else:
            # Error
            assert self.buy_button.state is True or self.sell_button.state is True, 'Neither the buy nor sell button was selected'

    #
    # Pubpen events to gather data
    #
    #@abstractmethod
    def handle_user_info(self, username, cash, *args):
        """Update the user's cash amount"""
        if 'user_info' in self._sub_ids:
            self.pubpen.unsubscribe(self._sub_ids['user_info'])
            del self._sub_ids['user_info']
        self.user_cash = cash

        self.validate_quantity()

    #@abstractmethod
    def handle_user_cash_update(self, new_cash, *args):
        """Update the user's cash amount"""
        self.user_cash = new_cash
        self.validate_quantity()

    #@abstractmethod
    def handle_market_update(self, commodity, price):
        """Update the price in the dialog if it's been updated on the backend"""
        if self.order is not None:
            if commodity == self.order.commodity:
                self.order.price = price
            self.dialog.set_title('{} - ${}'.format(commodity, price))

    #@abstractmethod
    def keypress(self, size, key):
        """Handle all keyboard shortcuts for the transaction dialog"""
        if key == 'esc':
            self.handle_transaction_finalized()
        #elif key == 'enter':
        #    self.handle_place_order()
        else:
            super().keypress(size, key)  #pylint: disable=not-callable
        return key


class CargoOrderDialog(OrderDialog):
    signals = ['close_cargo_order_dialog']

    def __init__(self, pubpen):
        self.free_space = 0
        self.commodity_in_hold = 0
        self.free_warehouse = 0
        self.commodity_in_warehouse = 0

        self.hold_box = CheckBox('Hold:', state=True)
        self.warehouse_box = CheckBox('Warehouse:', state=True)
        super().__init__(pubpen, (self.hold_box, self.warehouse_box))

        urwid.connect_signal(self.hold_box, 'postchange', self.validate_storage_toggle)
        urwid.connect_signal(self.warehouse_box, 'postchange', self.validate_storage_toggle)

        self.pubpen.subscribe('ship.info', self.handle_ship_info)
        self.pubpen.subscribe('ship.cargo.update', self.handle_cargo_update)

    @property
    def max_buy_quantity(self):
        """Maximum amount of a commodity that may be bought and not be invalid"""
        # Find out how much space we have available in the hold and local
        # warehouse
        available_space = 0
        if self.hold_box.state:
            available_space += self.free_space
        if self.warehouse_box.state:
            available_space += self.free_warehouse

        # maximum amount we can buy is the smaller of space available or cash/price
        return min(available_space, super().max_buy_quantity)

    @property
    def max_sell_quantity(self):
        """Maximum amount of a commodity that may be sold and not be invalid"""
        # Find how much of the commodity we have to sell
        amount = 0
        if self.hold_box.state:
            amount += self.commodity_in_hold
        if self.warehouse_box.state:
            amount += self.commodity_in_warehouse
        return amount

    #
    # Urwid event handlers for the dialog box widgets
    #
    def create_new_transaction(self, commodity, price, location):
        """Reset the dialog box whenever a new sale is started

        :arg commodity: The commodity that is being bought or sold
        :arg price: The amount that the commodity is selling for
        :arg location: The location the transaction is taking place
        """
        super().create_new_transaction(commodity, price, location)

        self.hold_box.set_state(True, do_callback=False)
        self.warehouse_box.set_state(True, do_callback=False)

        # recalculate hold and warehouse space
        self.pubpen.publish('query.ship.info')
        ### FIXME: Recalculate warehouse space
        pass

        #self.pubpen.subscribe('warehouse.{}.info', self.handle_warehouse_info)
        #self.pubpen.subscribe('warehouse.{}.cargo.update', self.handle_cargo_update)

    def handle_buy_sell_toggle(self, radio_button, new_state):
        """Change interface slightly depending on whether we're buying or selling"""
        super().handle_buy_sell_toggle(radio_button, new_state)

        ### FIXME: Implement warehouse
        if (radio_button is self.buy_button and new_state is True) or (radio_button is self.sell_button and new_state is False):
            self.hold_box.set_label('Hold: {} Free Space'.format(format_number(self.free_space)))
            #self.warehouse_box.set_label('Warehouse: {}'.format(format_number(self.free_warehouse)))
        else:
            self.hold_box.set_label('Hold: {} {}'.format(format_number(self.commodity_in_hold),
                                                         self.order.commodity))
            #self.warehouse_box.set_label('Warehouse: {}'.format(format_number(self.commodity_in_warehouse)))

    def validate_storage_toggle(self, checkbox, old_state):
        """Make sure that at least one of the hold/warehouse checkboxes is always checked"""
        # One of hold_box or warehouse must always be checked
        if checkbox == self.hold_box:
            if not self.warehouse_box:
                self.hold_box.set_state(True)
        else:
            if not self.hold_box:
                self.warehouse_box.set_state(True)

        # Recalculate maximums
        self.validate_quantity()

    #
    # Handlers for backend signals
    #
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

        # Recalculate maximums
        self.validate_quantity

    def handle_cargo_update(self, manifest, free_space, *args):
        """Update the hold space whenever we receive a cargo update event"""
        if self.free_space != free_space:
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

            # Recalculate maximums
            self.validate_quantity()


class EquipmentOrderDialog(OrderDialog):
    signals = ['close_eq_order_dialog']
    def __init__(self, pubpen):
        self.current_amount

        self.current_amount_label = urwid.Text('Current Amount:')
        super().__init__(pubpen,(self.current_amount_label,))
        pass

    @property
    def max_buy_quantity(self):
        """Return the maximum amount of a commodity that may be sold and not be invalid"""
        ### TODO: Each piece of equipment has different constraints on the maximum.
        # Lasers depend on the amount of weapon mounts in the ships
        # cargo and warehouse are unconstrained
        return super().max_buy_quantity

    @property
    def max_sell_quantity(self):
        """Return the maximum amount of a commodity that may be sold and not be invalid"""
        ### TODO: Each piece of equipment has different constraints on the maximum
        # Cargo is free_space // 100
        # warehouse is warehouse_free // 1000
        # lasers is total number of lasers
        return 0

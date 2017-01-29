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

import urwid

from .message_win import MsgType
from .numbers import format_number
from .order_dialog import OrderDialog
from .urwid_fixes import CheckBox

class CargoOrderDialog(OrderDialog):
    """Form to fill out to purchase or sell cargo at a market"""
    signals = ['close_cargo_order_dialog']

    def __init__(self, pubpen):
        self.free_space = 0
        self.commodity_in_hold = 0
        self.free_warehouse = 0
        self.commodity_in_warehouse = 0

        self.hold_box = CheckBox('Hold:', state=True)
        self.warehouse_box = CheckBox('Warehouse:', state=True)
        super().__init__(pubpen, 'ui.urwid.cargo_order_info',
                         (self.hold_box, self.warehouse_box))

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
        ### TODO: Recalculate warehouse space
        pass

        #self._sub_ids['warehouse_info'] = self.pubpen.subscribe('warehouse.{}.info', self.handle_warehouse_info)
        #self._sub_ids['warehouse'] = self.pubpen.subscribe('warehouse.{}.cargo.update', self.handle_cargo_update)

    def handle_buy_sell_toggle(self, radio_button, old_state):
        """Change interface slightly depending on whether we're buying or selling"""
        super().handle_buy_sell_toggle(radio_button, old_state)

        ### FIXME: Implement warehouse
        if self.buy_button.state:
            self.hold_box.set_label('Hold: {} Free Space'.format(format_number(self.free_space)))
            #self.warehouse_box.set_label('Warehouse: {}'.format(format_number(self.free_warehouse)))
        else:
            self.hold_box.set_label('Hold: {} {}'.format(format_number(self.commodity_in_hold),
                                                         self.order.commodity))
            #self.warehouse_box.set_label('Warehouse: {}'.format(format_number(self.commodity_in_warehouse)))

    def validate_storage_toggle(self, checkbox, old_state):
        """Make sure that at least one of the hold/warehouse checkboxes is always checked"""
        # One of hold_box or warehouse must always be checked
        allowed = True
        if checkbox == self.hold_box:
            if not self.warehouse_box.state:
                allowed = False
                self.hold_box.set_state(True, do_callback=False)
        else:
            if not self.hold_box.state:
                allowed = False
                self.warehouse_box.set_state(True, do_callback=False)

        if not allowed:
            self.pubpen.publish('ui.urwid.message',
                                'Not allowed to disable both hold and warehouse',
                                severity=MsgType.error)
        # Recalculate maximums
        self.validate_quantity()

    def handle_place_order(self, *args):
        """Request to make the transaction"""
        super().handle_place_order(*args)
        if self.order.buy:
            if self.hold_box.get_state() is True:
                ### TODO: place the min() of quantity or hold free space here.
                # put rest in warehouse
                self.order.hold_quantity = self.quantity.value()
            if self.warehouse_box.get_state() is True:
                ### TODO: implement warehouse
                pass
            ### TODO: if there's still more quantity, error?  (or reduce)
        else:
            if self.hold_box.get_state() is True:
                ### TODO: place the min() of quantity or amount of commodity in hold
                # take rest from warehouse
                self.order.hold_quantity = self.quantity.value()
            if self.warehouse_box.get_state() is True:
                ### TODO: implement warehouse
                pass

        self.pubpen.publish('action.user.order', self.order)

    #
    # Handlers for backend signals
    #
    def handle_ship_info(self, ship_type, free_space, filled_space, manifest):
        """Update the hold space """
        self.free_space = free_space

        commodity = ''
        if self.order is not None:
            commodity = self.order.commodity
            manifest_entry = manifest.get(commodity, None)
            self.commodity_in_hold = manifest_entry.quantity if manifest_entry else 0

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

            commodity = ''
            if self.order is not None:
                commodity = self.order.commodity
                if manifest.commodity == commodity:
                    self.commodity_in_hold = manifest.quantity

            if self.buy_button.state is True:
                self.hold_box.set_label('Hold: {} Free Space'.format(format_number(self.free_space)))
            else:
                self.hold_box.set_label('Hold: {} {}'.format(format_number(self.commodity_in_hold),
                                                             commodity))

            # Recalculate maximums
            self.validate_quantity()


class EquipOrderDialog(OrderDialog):
    """Form to fill out to purchase or sell equipment and property at a market"""
    signals = ['close_equip_order_dialog']

    def __init__(self, pubpen):
        self.current_amount = None
        self.free_space = 0
        self.free_warehouse = 0

        self.current_amount_label = urwid.Text('Current Amount:')
        super().__init__(pubpen, 'ui.urwid.equip_order_info',
                         extra_widgets=(self.current_amount_label,))

        self.pubpen.subscribe('ship.info', self.handle_ship_info)
        self.pubpen.subscribe('ship.cargo.update', self.handle_cargo_update)

    @property
    def max_buy_quantity(self):
        """Return the maximum amount of a commodity that may be sold and not be invalid"""
        if self.order is None:
            return 0

        if self.order.commodity.lower() in ('cargo module (100 units)', 'warehouse space (1000 units)'):
            return super().max_buy_quantity

        if self.order.commodity.lower() == 'laser array':
            ### TODO: Handle lasers
            # Lasers depend on the amount of weapon mounts in the ships
            return 0

        assert False, 'Unknown commodity %s' % self.order.commodity

    @property
    def max_sell_quantity(self):
        """Return the maximum amount of a commodity that may be sold and not be invalid"""
        if self.order is None:
            return 0

        if self.order.commodity.lower() == 'cargo module (100 units)':
            return self.free_space // 100

        if self.order.commodity.lower() == 'warehouse space (1000 units)':
            return self.free_warehouse // 1000

        if self.order.commodity.lower() == 'laser array':
            ### TODO: Handle lasers
            # lasers is total number of lasers on the ship
            return 0

    #
    # Handlers for backend signals
    #
    def handle_ship_info(self, ship_type, free_space, filled_space, manifest):
        """Update the hold space """
        if self.free_space != free_space:
            self.free_space = free_space

            # Recalculate maximums
            self.validate_quantity()

    def handle_cargo_update(self, manifest, free_space, *args):
        """Update the hold space whenever we receive a cargo update event"""
        if self.free_space != free_space:
            self.free_space = free_space

            # Recalculate maximums
            self.validate_quantity()

    def handle_place_order(self, *args):
        super().handle_place_order(*args)

        self.order.hold_quantity = self.quantity.value()
        self.pubpen.publish('action.user.order', self.order)

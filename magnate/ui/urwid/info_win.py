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
"""
The Info Window displays important stastics about hte player and player's ship.
"""

import urwid

from .numbers import format_number
from .urwid_fixes import LineBox


class InfoWindow(urwid.WidgetWrap):
    """Window to display a quick summary of some player information"""
    _selectable = False
    def __init__(self, pubpen):
        self.pubpen = pubpen
        self._location = None
        self._free_space = 0
        self._filled_space = 0
        self._warehouse_free = 0
        self._warehouse_used = 0
        self._cash = 0
        self._bank = 0
        self._loan = 0

        self._warehouse_sub_id = None
        #self._bank_sub_id = None
        ### FIXME: Implement bank, warehouse, bank, and loan
        header2 = urwid.Text('Ship Type:')
        self.ship_type_widget = urwid.Text('  ')
        header3 = urwid.Text('Free space:')
        self.free_space_widget = urwid.Text('  ')
        header4 = urwid.Text('Cargo:')
        self.filled_space_widget = urwid.Text('  ')
        header5 = urwid.Text('Warehouse:')
        self.warehouse_free_widget = urwid.Text('  ')
        header6 = urwid.Text('Transshipment:')
        self.warehouse_used_widget = urwid.Text('  ')
        header7 = urwid.Text('Cash:')
        self.cash_widget = urwid.Text('  ')
        header8 = urwid.Text('Bank:')
        self.bank_widget = urwid.Text('  ')
        header9 = urwid.Text('Loan:')
        self.loan_widget = urwid.Text('  ')
        info_list = urwid.SimpleListWalker([header2, self.ship_type_widget,
                                            header3, self.free_space_widget,
                                            header4, self.filled_space_widget,
                                            header5, self.warehouse_free_widget,
                                            header6, self.warehouse_used_widget,
                                            header7, self.cash_widget,
                                            header8, self.bank_widget,
                                            header9, self.loan_widget])
        info = urwid.ListBox(info_list)
        box = LineBox(info, tlcorner='─', trcorner='─', lline=' ', rline=None, bline=None)
        super().__init__(box)

        # Primary triggers: These are events that tell us we need to refresh
        # our information
        self.pubpen.subscribe('ship.moved', self.handle_new_location)
        self.pubpen.subscribe('ship.cargo.update', self.handle_cargo_update)
        self.pubpen.subscribe('ship.equip.update', self.handle_ship_update)
        self.pubpen.subscribe('user.cash.update', self.handle_cash_update)
        #self.pubpen.subscribe('user.bank.update')
        #self.pubpen.subscribe('user.loan.update')

        # Secondary triggers: These are responses to requests for information
        self.pubpen.subscribe('ship.info', self.handle_ship_info)
        self.pubpen.subscribe('user.info', self.handle_user_info)

        # Defer populating the initial values until a user has logged in
        self.pubpen.subscribe('user.login_success', self.populate_info)

    @property
    def free_space(self):
        return self._free_space

    @free_space.setter
    def free_space(self, new_value):
        self._free_space = new_value
        self.free_space_widget.set_text(' {}'.format(format_number(new_value)))

    @property
    def filled_space(self):
        return self._filled_space

    @filled_space.setter
    def filled_space(self, new_value):
        self._filled_space = new_value
        self.filled_space_widget.set_text(' {}'.format(format_number(new_value)))

    @property
    def cash(self):
        return self._cash

    @cash.setter
    def cash(self, new_value):
        self._cash = new_value
        self.cash_widget.set_text(' ${}'.format(format_number(new_value)))

    def populate_info(self, *args):
        """Populate the information for the first time"""
        self.pubpen.publish('query.user.info')
        self.pubpen.publish('query.ship.info')

    def handle_cargo_update(self, manifest, free_space, filled_space):
        """Update cargo information when it is updated in the backend"""
        self.free_space = free_space
        self.filled_space = filled_space

    def handle_cash_update(self, new_cash, *args):
        """Update cash display when cash is updated on the backend"""
        self.cash = new_cash

    def handle_new_location(self, location, *args):
        """Update the warehouse and finance information when we get to a new location"""
        if self._location == location:
            return
        # Unsubscribe old location triggers
        #if self._warehouse_sub_id is not None:
        #    self.pubpen.unsubscribe(self._warehouse_sub_id)
        #if self._bank_sub_id is not None:
        #    self.pubpen.unsubscribe(self._bank_sub_id)

        # Subscribe to new location triggers
        #self._warehouse_sub_id = self.pubpen.subscribe('warehouse.{}.info'.format(location))
        #self._bank_sub_id = self.pubpen.subscribe('bank.{}.info'.format(location))

        #self.pubpen.publish('query.warehouse.{}.info'.format(location))
        #self.pubpen.publish('query.bank.{}.info'.format(location))
        pass
        self._location = location

    def handle_ship_update(self, holdspace):
        """Update ship information when the ship gains or loses cargo space"""
        self.free_space = holdspace - self.filled_space

    def handle_ship_info(self, ship_type, free_space, filled_space, *args):
        """Update ship info for new ship info from the backend"""
        self.ship_type_widget.set_text(' {}'.format(ship_type))

        self.free_space = free_space
        self.filled_space = filled_space

    def handle_user_info(self, username, cash, location):
        """Update cash and location-dependent info for new user info"""
        self.cash = cash
        self.handle_new_location(location)

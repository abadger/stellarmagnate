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
from .sideless_linebox import SidelessLineBox


class InfoWindow(urwid.WidgetWrap):
    """Window to display a quick summary of some player information"""
    _selectable = False
    def __init__(self, pubpen):
        self.pubpen = pubpen
        self._location = None

        self._warehouse_sub_id = None
        #self._bank_sub_id = None
        ### FIXME: Implement bank, warehouse, bank, and loan
        header2 = urwid.Text('Ship Type:')
        self.ship_type = urwid.Text('  ')
        header3 = urwid.Text('Free space:')
        self.free_space = urwid.Text('  ')
        header4 = urwid.Text('Cargo:')
        self.filled_space = urwid.Text('  ')
        header5 = urwid.Text('Warehouse:')
        self.warehouse_free = urwid.Text('  ')
        header6 = urwid.Text('Transshipment:')
        self.warehouse_used = urwid.Text('  ')
        header7 = urwid.Text('Cash:')
        self.cash = urwid.Text('  ')
        header8 = urwid.Text('Bank:')
        self.bank = urwid.Text('  ')
        header9 = urwid.Text('Loan:')
        self.loan = urwid.Text('  ')
        info_list = urwid.SimpleListWalker([header2, self.ship_type,
                                            header3, self.free_space,
                                            header4, self.filled_space,
                                            header5, self.warehouse_free,
                                            header6, self.warehouse_used,
                                            header7, self.cash,
                                            header8, self.bank,
                                            header9, self.loan])
        info = urwid.ListBox(info_list)
        box = SidelessLineBox(info, tlcorner='─', trcorner='─', lline=' ', rline=None, bline=None)
        super().__init__(box)

        # Primary triggers: These are events that tell us we need to refresh
        # our information
        self.pubpen.subscribe('ship.moved', self.handle_new_location)
        ### FIXME: Subscribe to purchased, sold
        self.pubpen.subscribe('ship.cargo.update', self.handle_cargo_update)
        self.pubpen.subscribe('user.cash.update', self.handle_cash_update)
        #self.pubpen.subscribe('user.bank.update')
        #self.pubpen.subscribe('user.loan.update')

        # Secondary triggers: These are responses to requests for information
        self.pubpen.subscribe('ship.info', self.handle_ship_info)
        self.pubpen.subscribe('user.info', self.handle_user_info)

        # Defer populating the initial values until a user has logged in
        self.pubpen.subscribe('user.login_success', self.populate_info)

    def populate_info(self, *args):
        """Populate the information for the first time"""
        self.pubpen.publish('query.user.info')
        self.pubpen.publish('query.ship.info')

    def handle_cargo_update(self, manifest, free_space, filled_space):
        """Update cargo information when it is updated in the backend"""
        free_space = format_number(free_space)
        self.free_space.set_text(' {}'.format(free_space))

        filled_space = format_number(filled_space)
        self.filled_space.set_text(' {}'.format(filled_space))

    def handle_cash_update(self, new_cash, *args):
        """Update cash display when cash is updated on the backend"""
        self.cash.set_text(' ${}'.format(format_number(new_cash)))

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

    def handle_ship_info(self, ship_type, free_space, filled_space, *args):
        """Update ship info for new ship info from the backend"""
        self.ship_type.set_text(' {}'.format(ship_type))

        free_space = format_number(free_space)
        self.free_space.set_text(' {}'.format(free_space))

        filled_space = format_number(filled_space)
        self.filled_space.set_text(' {}'.format(filled_space))

    def handle_user_info(self, username, cash, location):
        """Update cash and location-dependent info for new user info"""
        self.cash.set_text(' ${}'.format(format_number(cash)))
        self.handle_new_location(location)

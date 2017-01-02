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
"""
Main window onto the Stellar Magnate Client

This handles the toplevel window and its direct subelements.
"""

from functools import partial

import urwid

from .gamemenu import GameMenuDialog
from .market import MarketDisplay, TransactionDialog
from .numbers import format_number
from .sideless_linebox import SidelessLineBox
from .travel import TravelDisplay

# ui elements:
# [x] Travel Menu
#     [x] Export signals for selecting entries
#     [x] hook up signal for opening the travel menu
#     [_] Jump
# [_] Menubar
#     [x] Basic entries
#     [_] Export signals for selecting the menu entries
#     [x] Travel
#     [_] Finance
#     [_] Market
#     [_] Shipyard
# [_] Game Menu
#   [x] Quit
#   [_] Save
#   [_] Load
# [_] commodities market
#   [_] Hold space
#   [_] Warehouse space
# [_] Commodities purchase
# [_] Info window
# [_] Financial menu
# [_] Financial  action menu
# [_] Fleet menu
# [_] Ship market
# [_] Ship purchase
# [_] Weapons market
# [_] Weapon purchase

class StatusBar(urwid.Columns):
    """Display a horizontal border with a field for username and location"""
    _selectable = False
    def __init__(self, pubpen, spacer=u'u2500'):
        self.pubpen = pubpen

        self.who = urwid.Text(u'\u2524 Name: \u251C')
        self.where = urwid.Text(u'\u2524 Location: \u251C')

        self.left = urwid.Columns([self.who])
        self.right = urwid.Columns([self.where])
        super().__init__((('pack', self.who),
                          ('weight', 1, urwid.Divider(spacer)),
                          ('pack', self.where),
                         ))

        # Connect to backend events
        self.pubpen.subscribe('user.info', self.handle_user_info)
        self.pubpen.subscribe('user.login_success', self.handle_login)
        self.pubpen.subscribe('ship.moved', self.handle_ship_moved)

    #
    # Widget methods
    #
    def update_username(self, username):
        """Update the user's name in the statusbar"""
        self.who.set_text('\u2524 Name: {} \u251C'.format(username))

    def update_location(self, location):
        """Update the ship's location in the statusbar"""
        self.where.set_text('\u2524 Location: {} \u251C'.format(location))

    #
    # Handlers
    #
    def handle_user_info(self, username, cash, location):
        """Update both username and location when we've explicitly requested the information"""
        self.update_username(username)
        self.update_location(location)

    def handle_login(self, username):
        """Update the user's name when they log in"""
        self.update_username(username)

    def handle_ship_moved(self, new_location, *args):
        """Update the ship's location when the ship moves"""
        self.update_location(new_location)


class MenuBar(urwid.WidgetWrap):
    """Menu displaying major player options"""
    _selectable = True

    def __init__(self, pubpen, line=u'\u2500'):
        self.pubpen = pubpen

        self.port_entry = urwid.Text('(P)ort District')
        self.yard_entry = urwid.Text('Ship(Y)ard')
        self.financial_entry = urwid.Text('(F)inancial')
        self.travel_entry = urwid.Text('(T)ravel')
        self.game_menu_entry = urwid.Text('(M)enu')

        self.menu_entries = urwid.Columns((
            ('weight', 1, urwid.Divider(' ')),
            ('pack', self.port_entry),
            ('pack', self.yard_entry),
            ('pack', self.financial_entry),
            ('pack', self.travel_entry),
            ('pack', self.game_menu_entry),
            ('weight', 1, urwid.Divider(' ')),
            ), dividechars=5)

        super().__init__(self.menu_entries)


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
        #self.pubpen.subscribe('ship.cargo.update')
        #self.pubpen.subscribe('user.cash.update')
        #self.pubpen.subscribe('user.bank.update')
        #self.pubpen.subscribe('user.loan.update')

        # Secondary triggers: These are responses to requests for information
        #self.pubpen.subscribe('ship.cargo.info')
        pass
        self.pubpen.subscribe('ship.info', self.handle_ship_info)
        self.pubpen.subscribe('user.info', self.handle_user_info)

        # Defer populating the initial values until a user has logged in
        self.pubpen.subscribe('user.login_success', self.populate_info)

    def populate_info(self, *args):
        # Populate the information for the first time
        self.pubpen.publish('query.user.info')
        self.pubpen.publish('query.ship.info')

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
        self.ship_type.set_text(' {}'.format(ship_type))

        free_space = format_number(free_space)
        self.free_space.set_text(' {}'.format(free_space))

        filled_space = format_number(filled_space)
        self.filled_space.set_text(' {}'.format(filled_space))

    def handle_user_info(self, username, cash, location):
        self.cash.set_text(' ${}'.format(cash))
        self.handle_new_location(location)


MAX_MESSAGES = 3
class MessageWindow(urwid.WidgetWrap):
    """Display system messages"""
    _MIN_TIME_BETWEEN_MESSAGES = 0.7
    _CAN_PRINT_MESSAGE = True

    def __init__(self, pubpen):
        self.pubpen = pubpen
        self.loop = self.pubpen.loop

        self.message_list = urwid.SimpleFocusListWalker([])
        list_box = urwid.ListBox(self.message_list)
        message_win = SidelessLineBox(list_box, tline=None, lline=None, bline=None,
                                      trcorner='│', brcorner='│')
        super().__init__(message_win)
        self.pubpen.subscribe('user.login_failure', self.add_message)
        self.pubpen.subscribe('user.order_failure', self.add_message)
        self.pubpen.subscribe('ship.movement_failure', self.add_message)

    def _allow_messages(self):
        self._CAN_PRINT_MESSAGE = True

    def add_message(self, msg):
        """
        Add a message to the MessageWindow.

        Reap older messages if there are too many
        """
        if not self._CAN_PRINT_MESSAGE:
            self.loop.call_later(self._MIN_TIME_BETWEEN_MESSAGES, self.add_message, msg)
            return

        self.message_list.append(urwid.Text(msg))
        while len(self.message_list) > MAX_MESSAGES:
            self.message_list.pop(0)

        self._CAN_PRINT_MESSAGE = False
        self.loop.call_later(self._MIN_TIME_BETWEEN_MESSAGES, self._allow_messages)


class ShipyardDisplay(urwid.WidgetWrap):
    """Display for the user to manage their ship and equipment"""
    _selectable = True

    def __init__(self, pubpen):
        self.pubpen = pubpen

        blank = urwid.Text('This test page intentionally left blank')
        container = urwid.Filler(blank)
        super().__init__(container)
        pass


class FinancialDisplay(urwid.WidgetWrap):
    """Display for the user to manage their bank and loan amounts"""
    _selectable = True

    def __init__(self, pubpen):
        self.pubpen = pubpen

        blank = urwid.Text('This test page intentionally left blank')
        container = urwid.Filler(blank)
        super().__init__(container)
        pass


class MainDisplay(urwid.WidgetWrap):
    """
    The MainDisplay is the main interaction point of the urwid interface

    MainDisplay changes as the user interacts with the interface, showing the
    market, commodity, travel menu etc.  Most of the user's active
    participation will be with the MainDisplay.
    """
    def __init__(self, pubpen):
        self.pubpen = pubpen
        self.display_stack = []
        self.blank = SidelessLineBox(urwid.SolidFill(' '), lline=None,
                                     blcorner='─', tlcorner='─',
                                     trcorner='\u252c', brcorner='\u2524')
        self.background = urwid.WidgetPlaceholder(self.blank)

        super().__init__(self.background)

        # Widgets traded in and out of the main display area

        self.market_display = MarketDisplay(self.pubpen)
        self.transaction_dialog = TransactionDialog(self.pubpen)
        self.travel_menu = TravelDisplay(self.pubpen)
        self.game_menu = GameMenuDialog(self.pubpen)
        self.shipyard_display = ShipyardDisplay(self.pubpen)
        self.financial_display = FinancialDisplay(self.pubpen)

        self.display_map = {
            'MarketDisplay': self.market_display,
            'TransactionDialog': self.transaction_dialog,
            'ShipyardDisplay': self.shipyard_display,
            'FinancialDisplay': self.financial_display,
            'TravelDisplay': self.travel_menu,
            'GameMenuDialog': self.game_menu,
            'Blank': self.blank
            }

        self.push_display('Blank')

        urwid.connect_signal(self.market_display, 'close_market_display', self.pop_display)
        urwid.connect_signal(self.market_display, 'open_transaction_dialog',
                             partial(self.push_display, 'TransactionDialog'))
        urwid.connect_signal(self.transaction_dialog, 'close_transaction_dialog', self.pop_display)
        urwid.connect_signal(self.travel_menu, 'close_travel_menu', self.pop_display)
        urwid.connect_signal(self.game_menu, 'close_game_menu', self.pop_display)

    def selectable(self):
        return True

    def push_display(self, display_name):
        """
        Push a new display to the top level

        Displays are like separate sheets of paper which we stack up on our
        desk.  We only have one instance of any given display in the stack but
        we can pull an old display to the top or we can decide we're done with
        the present display and go back to the previous one.
        """
        assert display_name in self.display_map
        widget = self.display_map[display_name]

        # Remove any prior instance of this display from the stack
        try:
            self.display_stack.remove(display_name)
        except ValueError:
            pass
        # Add the display at the end
        self.display_stack.append(display_name)
        self.background.original_widget = widget

    def pop_display(self, *args):
        """
        Remove a display from the stack.

        .. seealso::
            :meth:`~magnate.ui.urwid.mainwin.MainDisplay.push_display`
        """
        widget = None
        while widget is None:
            if len(self.display_stack) <= 1:
                widget = self.blank
            else:
                self.display_stack.pop()
                widget = self.display_map[self.display_stack[-1]]
                if widget in (self.game_menu, self.transaction_dialog):
                    # Never go back to the game menu
                    widget = None

        self.background.original_widget = widget

    def keypress(self, size, key):
        """
        Handle global keyboard shortcuts

        These keyboard shortcuts handle the toplevel menu which is always
        displayed.
        """
        if key == 'esc':
            self.pop_display()
        elif key in frozenset('pP'):
            self.push_display('MarketDisplay')
        elif key in frozenset('yY'):
            self.push_display('ShipyardDisplay')
        elif key in frozenset('fF'):
            self.push_display('FinancialDisplay')
        elif key in frozenset('tT'):
            self.push_display('TravelDisplay')
        elif key in frozenset('mM'):
            self.push_display('GameMenuDialog')
        else:
            super().keypress(size, key)  # pylint: disable=not-callable
        return


class MainWindow(urwid.LineBox):
    """Toplevel window mapping the top of the screen"""
    def __init__(self, pubpen):
        self.pubpen = pubpen

        #
        # Always displayed widgets
        #
        self.menu_bar = MenuBar(self.pubpen)
        self.info_window = InfoWindow(self.pubpen)
        self.main_display = MainDisplay(self.pubpen)
        self.msg_window = MessageWindow(self.pubpen)

        pile = urwid.Pile((self.main_display,
                           (MAX_MESSAGES, self.msg_window),
                          ))
        cols = urwid.Columns((pile, (15, self.info_window)))
        layout = urwid.Pile((
            ('pack', self.menu_bar),
            ('weight', 1, cols),
            ))
        self.top = urwid.Frame(layout)

        super().__init__(self.top)

        tline = self.tline_widget[0]
        self.status_bar = StatusBar(self.pubpen, spacer=tline.div_char)

        self.tline_widget.contents.clear()
        self.tline_widget.contents.extend((
            (tline, self.tline_widget.options('given', 1, False)),
            (self.status_bar, self.tline_widget.options('weight', 1, False)),
            (tline, self.tline_widget.options('given', 1, False)),
            ))

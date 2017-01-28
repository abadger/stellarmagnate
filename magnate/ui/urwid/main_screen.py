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
Main window onto the Stellar Magnate Client

This handles the toplevel window and its direct subelements.
"""

from functools import partial

import urwid

from .cargo_order_dialog import CargoOrderDialog, EquipOrderDialog
from .gamemenu_dialog import GameMenuDialog
from .info_win import InfoWindow
from .market_display import MarketDisplay
from .menu_bar_win import MenuBarWindow
from .message_win import MessageWindow
from .port_display import PortDisplay
from .travel_display import TravelDisplay
from .urwid_fixes import LineBox

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
#     [x] Market
#     [_] Port
# [_] Game Menu
#   [x] Quit
#   [_] Save
#   [_] Load
# [_] commodities market
#   [x] Hold space
#   [_] Warehouse space
# [_] Info window
#   [_] Warehouse
#   [-] Bank
#   [_] Loan
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


class FinancialDisplay(urwid.WidgetWrap):
    """Display for the user to manage their bank and loan amounts"""
    _selectable = True

    def __init__(self, pubpen):
        self.pubpen = pubpen

        blank = urwid.Text('This test page intentionally left blank')
        container = urwid.Filler(blank)
        super().__init__(container)
        pass


class MainWindow(urwid.WidgetWrap):
    """
    The MainWindow is the main interaction point of the urwid interface

    MainWindow changes as the user interacts with the interface, showing the
    market, commodity, travel menu etc.  Most of the user's active
    participation will be with the MainWindow.
    """
    def __init__(self, pubpen):
        self.pubpen = pubpen
        self.display_stack = []
        self.blank = LineBox(urwid.SolidFill(' '), lline=None,
                             blcorner='─', tlcorner='─',
                             trcorner='\u252c', brcorner='\u2524')
        self.background = urwid.WidgetPlaceholder(self.blank)

        super().__init__(self.background)

        # Widgets traded in and out of the main display area

        self.market_display = MarketDisplay(self.pubpen)
        self.cargo_order_dialog = CargoOrderDialog(self.pubpen)
        self.travel_menu = TravelDisplay(self.pubpen)
        self.game_menu = GameMenuDialog(self.pubpen)
        self.port_display = PortDisplay(self.pubpen)
        self.equip_order_dialog = EquipOrderDialog(self.pubpen)
        self.financial_display = FinancialDisplay(self.pubpen)

        self.display_map = {
            'MarketDisplay': self.market_display,
            'CargoOrderDialog': self.cargo_order_dialog,
            'PortDisplay': self.port_display,
            'EquipOrderDialog': self.equip_order_dialog,
            'FinancialDisplay': self.financial_display,
            'TravelDisplay': self.travel_menu,
            'GameMenuDialog': self.game_menu,
            'Blank': self.blank
            }

        self.dialogs = frozenset(n for n in self.display_map if n.endswith('Dialog'))

        self.push_display('Blank')

        urwid.connect_signal(self.market_display, 'close_market_display', self.pop_display)
        urwid.connect_signal(self.market_display, 'open_cargo_order_dialog',
                             partial(self.push_display, 'CargoOrderDialog'))
        urwid.connect_signal(self.cargo_order_dialog, 'close_cargo_order_dialog', self.pop_display)
        urwid.connect_signal(self.port_display, 'open_equip_order_dialog',
                             partial(self.push_display, 'EquipOrderDialog'))
        urwid.connect_signal(self.equip_order_dialog, 'close_equip_order_dialog', self.pop_display)
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

        if self.display_stack and self.display_stack[-1] in self.dialogs:
            # Never go back to dialogs.  So we need to finalize them and
            # remove them from the stack when we move to a different
            # display
            dialog = self.display_map[self.display_stack.pop()]
            dialog.finalize()

        # Add the display at the end
        self.display_stack.append(display_name)
        self.background.original_widget = widget

    def pop_display(self, *args):
        """
        Remove a display from the stack.

        .. seealso::
            :meth:`~magnate.ui.urwid.mainwin.MainWindow.push_display`
        """
        widget = None
        while widget is None:
            if len(self.display_stack) <= 1:
                widget = self.blank
            else:
                self.display_stack.pop()
                widget = self.display_map[self.display_stack[-1]]

        self.background.original_widget = widget

    def keypress(self, size, key):
        """
        Handle global keyboard shortcuts

        These keyboard shortcuts handle the toplevel menu which is always
        displayed.
        """
        if key == 'esc':
            self.pop_display()
        elif key in frozenset('cC'):
            self.push_display('MarketDisplay')
        elif key in frozenset('pP'):
            self.push_display('PortDisplay')
        elif key in frozenset('fF'):
            self.push_display('FinancialDisplay')
        elif key in frozenset('tT'):
            self.push_display('TravelDisplay')
        elif key in frozenset('mM'):
            self.push_display('GameMenuDialog')
        else:
            super().keypress(size, key)  # pylint: disable=not-callable
        return


class MainScreen(urwid.LineBox):
    """Toplevel window mapping the top of the screen"""
    def __init__(self, pubpen):
        self.pubpen = pubpen

        #
        # Always displayed widgets
        #
        self.menu_bar_window = MenuBarWindow(self.pubpen)
        self.info_window = InfoWindow(self.pubpen)
        self.main_window = MainWindow(self.pubpen)
        self.msg_window = MessageWindow(self.pubpen)

        pile = urwid.Pile((self.main_window,
                           (self.msg_window.height, self.msg_window),
                          ))
        cols = urwid.Columns((pile, (15, self.info_window)))
        layout = urwid.Pile((
            ('pack', self.menu_bar_window),
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

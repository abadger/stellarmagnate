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

from functools import partial

import urwid

from .gamemenu import GameMenuDialog
from .market import MarketDisplay, TransactionDialog
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
        self.who.set_text('\u2524 Name: {} \u251C'.format(username))

    def update_location(self, location):
        self.where.set_text('\u2524 Location: {} \u251C'.format(location))

    #
    # Handlers
    #
    def handle_user_info(self, username, cash, location):
        self.update_username(username)
        self.update_location(location)

    def handle_login(self, username):
        self.update_username(username)

    def handle_ship_moved(self, new_location, old_location):
        self.update_location(new_location)


class MenuBar(urwid.Pile):
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

        super().__init__((
            ('pack', self.menu_entries),
            ('weight', 1, urwid.Divider(line)),
            ))


class InfoWindow(urwid.WidgetWrap):
    _selectable = False
    def __init__(self, pubpen):
        self.pubpen = pubpen

        self._warehouse_sub_id = None
        #self._bank_sub_id = None
        ### FIXME: Implement bank, warehouse, bank, and loan
        header1 = urwid.Text('Ship:')
        self.ship_name = urwid.Text('  ')
        header2 = urwid.Text('Ship Type:')
        self.ship_type = urwid.Text('  ')
        header3 = urwid.Text('Free space:')
        self.hold_free = urwid.Text('  ')
        header4 = urwid.Text('Cargo:')
        self.hold_used = urwid.Text('  ')
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
        info_list = urwid.SimpleListWalker([header1, self.ship_name,
                                            header2, self.ship_type,
                                            header3, self.hold_free,
                                            header4, self.hold_used,
                                            header5, self.warehouse_free,
                                            header6, self.warehouse_used,
                                            header7, self.cash,
                                            header8, self.bank,
                                            header9, self.loan])
        info = urwid.ListBox(info_list)
        super().__init__(info)

        # Primary triggers: These are events that tell us we need to refresh
        # our information
        self.pubpen.subscribe('ship.moved', self.handle_new_location)
        ### FIXME: Subscribe to purchased, sold
        #self.pubpen.subscribe('ship.cargo.update')
        #self.pubpen.subscribe('user.cash.update')
        #self.pubpen.subscribe('user.bank.update')
        #self.pubpen.subscribe('user.loan.update')

        # Secondary triggers: These are responses to requests for information
        #self.pubpen.subscribe('ship.info')
        #self.pubpen.subscribe('ship.cargo.info')
        #self.pubpen.subscribe('user.info')
        pass

    def handle_new_location(self, location, *args):
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


class ShipyardDisplay(urwid.WidgetWrap):
    _selectable = True

    def __init__(self, pubpen):
        self.pubpen = pubpen

        blank = urwid.Text('This test page intentionaly left blank')
        container = urwid.Filler(blank)
        super().__init__(container)
        pass


class FinancialDisplay(urwid.WidgetWrap):
    _selectable = True

    def __init__(self, pubpen):
        self.pubpen = pubpen

        blank = urwid.Text('This test page intentionaly left blank')
        container = urwid.Filler(blank)
        super().__init__(container)
        pass


class MainDisplay(urwid.WidgetWrap):
    def __init__(self, pubpen):
        self.pubpen = pubpen
        self.display_stack = []
        self.blank = urwid.LineBox(urwid.SolidFill(' '))
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
    def __init__(self, pubpen):
        self.pubpen = pubpen

        #
        # Always displayed widgets
        #
        self.menu_bar = MenuBar(self.pubpen)
        self.info_window = InfoWindow(self.pubpen)
        self.main_display = MainDisplay(self.pubpen)

        cols = urwid.Columns([self.main_display, (15, self.info_window)])
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

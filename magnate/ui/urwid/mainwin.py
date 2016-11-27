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

import itertools
import string

import urwid

# ui elements:
# [x] Splash
# [x] Status bar
#     [x] Hook up signals to change User and Location
# [x] Travel Menu
#     [x] Export signals for selecting entries
#     [x] hook up signal for opening the travel menu
# [_] Menubar
#     [_] Export signals for selecting the menu entries
# [_] Game Menu
# [_] Info window
# [_] Financial menu
# [_] Financial  action menu
# [_] Fleet menu
# [_] Ship market
# [_] Ship purchase
# [_] Weapons market
# [_] Weapon purchase
# [_] commodities market
# [_] Commodities purchase

class StatusBar(urwid.Columns):
    _selectable = False
    def __init__(self, pubpen, spacer=u'u2500'):
        self.pubpen = pubpen

        self.who = urwid.Text('{} Name: '.format(spacer))
        self.where = urwid.Text(' Location: {}'.format(spacer))

        self.left = urwid.Columns([self.who])
        self.right = urwid.Columns([self.where])
        super().__init__((('pack', self.who),
            ('weight', 1, urwid.Divider(spacer)),
            ('pack', self.where),
            ))

        #
        # Connect to backend events
        #

        self.pubpen.subscribe('user.info', self.handle_user_info)
        self.pubpen.subscribe('user.login_success', self.handle_login)
        self.pubpen.subscribe('ship.moved', self.handle_ship_moved)

    #
    # Widget methods
    #

    def update_username(self, username):
        self.who.set_text(' Name: {} '.format(username))

    def update_location(self, location):
        self.where.set_text(' Location: {} '.format(location))

    #
    # Handlers
    #

    def handle_user_info(self, username, cash, location):
        self.update_username(username)
        self.update_location(location)

    def handle_login(self, username):
        self.update_username(username)

    def handle_ship_moved(self, old_location, new_location):
        self.update_location(new_location)


class MenuBar(urwid.Pile):
    _selectable = True

    def __init__(self, pubpen, line=u'\u2500'):
        self.pubpen = pubpen

        self.port_entry = urwid.Text('(P)ort District')
        self.yard_entry = urwid.Text('Ship(Y)ard')
        self.financial_entry = urwid.Text('(F)inancial')
        self.travel_entry = urwid.Text('(T)ravel')
        self.game_menu_entry = urwid.Text('M(e)nu')

        self.menu_entries = urwid.Columns((
            ('weight', 1, urwid.Divider(' ')),
            ('pack', self.port_entry),
            ('pack', self.yard_entry),
            ('pack', self.financial_entry),
            ('pack', self.travel_entry),
            ('pack', self.game_menu_entry),
            ('weight', 1, urwid.Divider(' ')),
            ), dividechars=3)

        super().__init__((
            ('pack', self.menu_entries),
            ('weight', 1, urwid.Divider(line)),
            ))


class TravelMenu(urwid.ListBox):
    _selectable = True
    signals = ['close_travel_menu']

    idx_names = [str(c) for c in itertools.chain(range(1, 9), [0], (c for c in string.punctuation if c not in frozenset('(){}[]<>')))]

    def __init__(self, pubpen):
        self.pubpen = pubpen

        self.listwalker = urwid.SimpleFocusListWalker([])
        super().__init__(self.listwalker)
        self.pubpen.subscribe('ship.destinations', self.handle_new_destinations)

    def handle_new_destinations(self, locations):
        self.listwalker.clear()
        self.keypress_map = {}
        for idx, location in enumerate(locations):
            self.listwalker.append(urwid.Text('({}) {}'.format(self.idx_names[idx], location)))
            self.keypress_map[self.idx_names[idx]] = location

    def handle_new_location(self, old_location, location):
        self.pubpen.unsubscribe(self.ship_moved_sub_id)
        urwid.emit_signal(self, 'close_travel_menu')

    def keypress(self, size, key):
        if key in self.keypress_map:
            destination = self.keypress_map[key]
            self.ship_moved_sub_id = self.pubpen.subscribe('ship.moved', self.handle_new_location)
            self.pubpen.emit('action.ship.movement_attempt', destination)
            return
        super().keypress(size, key)
        return key


class InfoWindow(urwid.Pile):
    _selectable = False
    def __init__(self, pubpen):
        super().__init__([])
        pass


class MarketMenu(urwid.Pile):
    _selectable = True
    def __init__(self, pubpen):
        super().__init__([])
        pass


class MainWindow(urwid.LineBox):
    def __init__(self, pubpen):
        self.pubpen = pubpen

        #
        # Always displayed widgets
        #
        self.menu_bar = MenuBar(self.pubpen)
        self.info_window = InfoWindow(self.pubpen)
        self.main_display = urwid.Pile((
            ('pack', self.menu_bar),
            ('pack', urwid.Text(' ')),
            ))
        self.top = urwid.Frame(self.main_display)

        super().__init__(self.top)

        tline = self.tline_widget[0]
        self.status_bar = StatusBar(self.pubpen, spacer=tline.div_char)

        self.tline_widget.contents.clear()
        self.tline_widget.contents.extend((
            (tline, self.tline_widget.options('given', 1, False)),
            (self.status_bar, self.tline_widget.options('weight', 1, False)),
            (tline, self.tline_widget.options('given', 1, False)),
            ))

        #
        # Widgets traded in and out of the main display area
        #

        self.travel_menu = TravelMenu(self.pubpen)
        self.market_menu = MarketMenu(self.pubpen)

        urwid.connect_signal(self.travel_menu, 'close_travel_menu', self.display_market_menu)

    def selectable(self):
        # Decoration widgets like LineBox override selectable() so we need to
        # use an actual method
        return True

    def toplevel_input(self, key):
        raise urwid.ExitMainLoop()

    def display_travel_menu(self):
        self.main_display.contents[1] = (self.travel_menu, self.main_display.options(height_type='weight', height_amount=20))
        self.main_display.focus_position = 1

    def display_market_menu(self):
        self.main_display.contents[1] = (self.market_menu, self.main_display.options(height_type='weight', height_amount=20))
        self.main_display.focus_position = 1

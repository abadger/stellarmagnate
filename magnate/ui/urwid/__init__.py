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


class TitleCard(urwid.LineBox):
    """Display a splash screen"""
    signals = ['close_title_card']

    def __init__(self, pubpen):
        self.pubpen = pubpen

        program_name = urwid.Text('Stellar Magnate', align='center')
        copyright_name = urwid.Text('(C) 2016, Toshio Kuratomi', align='center')
        license = urwid.Text('GNU General Public License 3.0 or later', align='center')
        screen = urwid.Filler(urwid.Pile([program_name, copyright_name, license]), valign='middle')
        super().__init__(screen)

    def keypress(self, *args):
        urwid.emit_signal(self, 'close_title_card')

    def selectable(self):
        # Decoration widgets like LineBox override selectable() so we need to
        # use an actual method
        return True


class LoginScreen(urwid.WidgetWrap):
    signals = ['logged_in']

    def __init__(self, pubpen):
        self.pubpen = pubpen

        # Grid widget
        # label: Username    # entrybox
        # label: Password    # entrybox
        username_label = urwid.Text('Username: ', align='right')
        password_label = urwid.Text('Password: ', align='right')
        self.username = urwid.Edit()
        self.password = urwid.Edit()
        self.quit_button = urwid.Button('Quit')
        self.login_button = urwid.Button('Login')
        self.buttons = urwid.Columns((
            (len('Quit') + 4, self.quit_button),
            (len('Login') + 4, self.login_button),
            ), focus_column=1)

        labels = urwid.Pile([username_label, password_label])
        self.fields = urwid.Pile([self.username, self.password, self.buttons], focus_item=0)
        entry_box = urwid.Columns([labels, self.fields])
        self.display = urwid.Filler(entry_box,  valign='middle')
        decorate = urwid.LineBox(self.display)
        super().__init__(decorate)

        self.focusable_widgets = (w for w in itertools.cycle((
            ((self.fields, 1),),
            ((self.fields, 2), (self.buttons, 1)),
            ((self.fields, 2), (self.buttons, 0)),
            ((self.fields, 0),)
            )))

        urwid.connect_signal(self.login_button, 'click', self.attempt_login)
        urwid.connect_signal(self.quit_button, 'click', self.quit)
        self.pubpen.subscribe('user.login_success', self.handle_login_success)
        self.pubpen.subscribe('user.login_failure', self.handle_login_failure)

#    def selectable(self):
#        # Decoration widgets like LineBox override selectable() so we need to
#        # use an actual method
#        return True
#
    def logged_in(self, username):
        urwid.emit_signal(self, 'logged_in')

    def reset(self):
        self.username.set_edit_text('')
        self.password.set_edit_text('')
        self.fields.focus_position = 0

    def attempt_login(self, *args):
        self.pubpen.emit('action.user.login_attempt', self.username.get_text()[0], self.password.get_text()[0])

    def quit(self, button):
        raise urwid.ExitMainLoop()

    def handle_login_success(self, username):
        self.reset()
        self.logged_in(username)

    def handle_login_failure(self, username):
        self.reset()


    def keypress(self, size, key):
        super().keypress(size, key)
        if key == 'enter':
            self.attempt_login()
            return
        elif key == 'tab':
            focus_paths = next(self.focusable_widgets)
            for widget, position in focus_paths:
                widget.focus_position = position
            return
        return key

class Interface:
    def __init__(self, pubpen):
        self.pubpen = pubpen

        #
        # Windows
        #

        self.title_card = TitleCard(pubpen)
        self.login_screen = LoginScreen(pubpen)
        self.main_window = MainWindow(pubpen)
        self.root_win = urwid.Frame(self.title_card)

        #
        # Arrange the widgets
        #

        self.show_title_card()

        #
        # Connect to UI events
        #

        urwid.connect_signal(self.title_card, 'close_title_card', self.show_login_screen)
        urwid.connect_signal(self.login_screen, 'logged_in', self.show_main_window)

        #
        # Connect to selected backend events
        #

        pass
        #
        # Setup the main loop
        #

        self.urwid_loop = urwid.MainLoop(self.root_win,
                event_loop=urwid.AsyncioEventLoop(loop=self.pubpen.loop),
                unhandled_input=self.toplevel_input)

    def show_title_card(self):
        self.root_win.body = self.title_card

    def show_login_screen(self):
        self.root_win.body = self.login_screen

    def show_main_window(self):
        self.root_win.body = self.main_window

    def toplevel_input(self, keypress):
        if self.root_win.body == self.main_window:
            if keypress in frozenset('tT'):
                self.main_window.display_travel_menu()
                return
        elif self.root_win.body == self.title_card:
            # Let the title card handle all input
            return
        elif self.root_win.body == self.login_screen:
            # Login screen handles all of its own input
            return
        raise urwid.ExitMainLoop()

    def run(self):
        self.urwid_loop.run()

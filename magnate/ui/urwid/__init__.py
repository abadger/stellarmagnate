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

import urwid

from magnate.ui.api import UserInterface
from .auth import LoginScreen
from .mainwin import MainWindow
from .title import TitleCard


class Interface(UserInterface):
    def __init__(self, pubpen):
        self.pubpen = pubpen

        # Windows

        self.title_card = TitleCard(pubpen)
        self.login_screen = LoginScreen(pubpen)
        self.main_window = MainWindow(pubpen)
        self.root_win = urwid.Frame(self.title_card)

        # Arrange the widgets

        self.show_title_card()

        # Connect to UI events

        urwid.connect_signal(self.title_card, 'close_title_card', self.show_login_screen)
        urwid.connect_signal(self.login_screen, 'logged_in', self.show_main_window)

        # Setup the main loop

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

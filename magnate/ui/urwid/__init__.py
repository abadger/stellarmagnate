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
        self.root_win = urwid.Frame(urwid.SolidFill(' '))

        # Arrange the widgets

        self.show_title_card()

        # Connect to UI events

        urwid.connect_signal(self.title_card, 'close_title_card', self.show_login_screen)
        urwid.connect_signal(self.login_screen, 'logged_in', self.show_main_window)

        # Setup the main loop

        self.urwid_loop = urwid.MainLoop(self.root_win,
                event_loop=urwid.AsyncioEventLoop(loop=self.pubpen.loop),
                unhandled_input=self.toplevel_input,
                palette=(
                    ('reversed', 'standout', ''),
                    ),
                )

    def show_title_card(self):
        self.root_win.body = urwid.Filler(self.title_card, height=('relative', 100))

    def show_login_screen(self):
        self.root_win.body = self.login_screen
        self.root_win.body = urwid.Filler(self.login_screen, height=('relative', 100))

    def show_main_window(self):
        self.root_win.body = urwid.Filler(self.main_window, height=('relative', 100))

    def toplevel_input(self, keypress):
        # The screens are each responsible for their own input
        return

    def run(self):
        self.urwid_loop.run()

# Stellar Magnate - A space-themed commodity trading game
# Copyright (C) 2016, 2018 Toshio Kuratomi <toshio@fedoraproject.org>
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
The main entrypoint into the urwid user interface
"""

import urwid

from magnate.logging import log
from magnate.ui.api import UserInterface
from .auth_screen import LoginScreen
from .game_select_screen import GameSelectScreen
from .main_screen import MainScreen
from .title_screen import TitleScreen


mlog = log.fields(mod=__name__)


class Interface(UserInterface):
    """The main entrypoint into the urwid user interface

    Creates the main widgets and takes care of switching between them.
    """
    def __init__(self, pubpen, cli_args):
        flog = mlog.fields(func='Interface.__init__')
        flog.fields(pubpen=pubpen, cli_args=cli_args).info('Creating UserInterface')

        super().__init__(pubpen, cli_args)

        # Note: We don't have any extra command line args

        # Windows
        flog.debug('Creating toplevel screens')
        self.title_card = TitleScreen(pubpen)
        self.login_screen = LoginScreen(pubpen)
        self.game_select_screen = GameSelectScreen(pubpen)
        self.main_window = MainScreen(pubpen)
        self.root_win = urwid.Frame(urwid.SolidFill(' '))

        # Arrange the widgets
        flog.debug('display the splash screen')
        self.show_title_card()

        # Connect to UI events
        flog.debug('connecting screen switching urwid signals')
        urwid.connect_signal(self.title_card, 'close_title_card', self.show_login_screen)
        urwid.connect_signal(self.login_screen, 'logged_in', self.show_game_select_screen)
        urwid.connect_signal(self.game_select_screen, 'game_selected', self.show_main_window)
        #urwid.connect_signal(self.game_select_screen, 'new_game', self.show_main_window)

        # Setup the main loop
        flog.debug('setup urwid mainloop')
        self.urwid_loop = urwid.MainLoop(self.root_win,
                                         event_loop=urwid.AsyncioEventLoop(loop=self.pubpen.loop),
                                         palette=(('reversed', 'standout', ''),),)

        flog.info('urwid interface setup complete')

    def show_title_card(self):
        """Display a splash screen"""
        flog = mlog.fields(func='Interface.show_title_card')
        flog.info('Show splash screen')
        self.root_win.body = urwid.Filler(self.title_card, height=('relative', 100))

    def show_login_screen(self):
        """Display a login form"""
        flog = mlog.fields(func='Interface.show_login_screen')
        flog.info('Show login screen')
        self.root_win.body = urwid.Filler(self.login_screen, height=('relative', 100))

    def show_game_select_screen(self):
        """Display a form to load a game"""
        flog = mlog.fields(func='Interface.show_game_select_screen')
        flog.info('Show game select screen')
        self.root_win.body = urwid.Filler(self.game_select_screen, height=('relative', 100))

    def show_main_window(self):
        """Display the main window"""
        flog = mlog.fields(func='Interface.show_main_window')
        flog.info('Show the main window')
        self.root_win.body = urwid.Filler(self.main_window, height=('relative', 100))

    def run(self):
        flog = mlog.fields(func='Interface.run')
        flog.info('Run the Urwid Interface main loop')
        self.urwid_loop.run()
        flog.info('Leaving the Urwid interface')

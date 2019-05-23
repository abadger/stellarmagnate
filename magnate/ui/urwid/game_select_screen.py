# Stellar Magnate - A space-themed commodity trading game
# Copyright (C) 2018 Toshio Kuratomi <toshio@fedoraproject.org>
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
Select a save game Screen widget
"""

import itertools
from functools import partial

import urwid


# Things to do here:
# * When a user logs in, update the save game list
# * display the list of savegames in a menu with the option for New game appended
# * If new game is selected, ask the backend to start a new game
# * If a save game is selected, ask the backend to load that save game


class GameSelectScreen(urwid.WidgetWrap):
    """
    Screen that prompts the user for a savegame
    """
    signals = ['game_selected']

    def __init__(self, pubpen):
        self.pubpen = pubpen

        self.listwalker = urwid.SimpleFocusListWalker([])
        box = urwid.ListBox(self.listwalker)
        outer_layout = urwid.LineBox(box)
        super().__init__(outer_layout)

        self.pubpen.subscribe('user.list_save_games', self.handle_save_files)

        # Everytime a different user is logged in, request the list of savegames
        self.pubpen.subscribe('user.login_success', self.request_savegames)

    def request_savegames(self, username):
        """Request the list of savegames"""
        self.pubpen.publish('query.game.list_save_games', self.handle_save_files)

    def handle_save_files(self, game_files):
        """Update the save file list when the file opens"""

        self.listwalker.clear()
        button = urwid.Button("Start New Game")
        self.listwalker.append(urwid.AttrMap(button, None, focus_map='reversed'))
        urwid.connect_signal(button, 'click', self.handle_new_game)

        for game_info in game_files:
            button = urwid.Button(f"{game_info['player']}, {game_info['date']}: {game_info['cash']}")
            self.listwalker.append(urwid.AttrMap(button, None, focus_map='reversed'))
            urwid.connect_signal(button, 'click', partial(self.handle_button_click, game_info['filename']))

    def handle_new_game(self):
        # Popup a form to get savegame name, captain name, ship name
        pass

        savegame = 'toshio-save1'
        captain = 'Hiormi'
        ship = 'Minnow'

        self.pubpen.subscribe('user.new_game_success', self.handle_load_success)
        self.pubpen.subscribe('user.new_game_failure', self.handle_load_failure)
        self.pubpen.publish('user.create_new_game', savegame, captain, ship)

    def handle_button_click(self, savefile):
        """When a savefile is clicked, attempt to load it"""
        self.pubpen.subscribe('user.load_success', self.handle_load_success)
        self.pubpen.subscribe('user.load_failure', self.handle_load_failure)

        self.pubpen.publish('user.load_game', savefile)

    def loaded_game(self, username):
        """Tell the main window that we've loaded a game"""
        urwid.emit_signal(self, 'game_selected')

    def reset(self):
        """Reset the savegame form"""
        self.savefile.set_edit_text('')
        self.fields.focus_position = 0

    def attempt_load_game(self, *args):
        """Notify the dispatcher to attempt to load a game"""
        self.pubpen.publish('action.game.load_game',
                            self.savefile.get_text()[0])

    def handle_load_success(self, username):
        """Show that the game has been loaded"""
        self.reset()
        self.loaded_game(username)

    def handle_load_failure(self, username):
        """Handle a failure loading a game"""
        self.reset()
        self.status_message.set_text(('reversed', 'Failed to load game'))

    def keypress(self, size, key):
        """Handle cycling through inputs and submitting load data"""
        super().keypress(size, key)

        if key == 'enter':
            self.attempt_load_game()
            return

        if key == 'tab':
            focus_paths = next(self.focusable_widgets)
            for widget, position in focus_paths:
                widget.focus_position = position
            return

        return key

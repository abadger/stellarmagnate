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
Game Menu widget
"""
import urwid

from .sideless_linebox import SidelessLineBox

class GameMenuDialog(urwid.WidgetWrap):
    """
    Menu for Meta-game entries

    Saving, quiting, settings, etc

    """
    _selectable = True
    signals = ['close_game_menu']

    def __init__(self, pubpen):
        self.pubpen = pubpen

        self.save_button = urwid.Button('(S)ave')
        self.load_button = urwid.Button('(L)oad')
        self.quit_button = urwid.Button('(Q)uit')
        self.continue_button = urwid.Button('(ESC) Continue Game')

        self.buttons = urwid.SimpleFocusListWalker((
            urwid.AttrMap(self.save_button, None, focus_map='reversed'),
            urwid.AttrMap(self.load_button, None, focus_map='reversed'),
            urwid.AttrMap(self.quit_button, None, focus_map='reversed'),
            urwid.AttrMap(self.continue_button, None, focus_map='reversed'),
            ))
        self.entrybox = urwid.ListBox(self.buttons)

        # Draw a box around the widget and constrain the widget's size
        linebox = urwid.LineBox(self.entrybox, tlcorner='\u2554',
                                tline='\u2550', trcorner='\u2557',
                                blcorner='\u255A', bline='\u2550',
                                brcorner='\u255D', lline='\u2551',
                                rline='\u2551')
        padding = urwid.Padding(linebox, align='center',
                                width=len(self.continue_button.get_label()) + 6)
        filler = urwid.Filler(padding, valign='middle',
                              height=len(self.buttons) + 2)

        outer_layout = SidelessLineBox(filler, lline=None, blcorner='─',
                                       tlcorner='─', trcorner='\u252c',
                                       brcorner='\u2524')
        super().__init__(outer_layout)

        urwid.connect_signal(self.save_button, 'click', self.save_game)
        urwid.connect_signal(self.load_button, 'click', self.load_game)
        urwid.connect_signal(self.quit_button, 'click', self.quit_client)
        urwid.connect_signal(self.continue_button, 'click', self.continue_game)

    def save_game(self, *args):
        """Save game state to a file"""
        pass

    def load_game(self, *args):
        """Load game state from a file"""
        pass

    @staticmethod
    def quit_client(*args):
        """Quit the game"""
        raise urwid.ExitMainLoop()

    def continue_game(self, *args):
        """Close the game menu and continue playing"""
        urwid.emit_signal(self, 'close_game_menu')

    def keypress(self, size, key):
        """Process keyboard shortcuts for the GameMenu"""
        super().keypress(size, key) # pylint: disable=not-callable
        if key in frozenset('sS'):
            self.save_game()
        elif key in frozenset('lL'):
            self.load_game()
        elif key in frozenset('qQ'):
            self.quit_client()

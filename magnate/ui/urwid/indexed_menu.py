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
Helpful code for creating menus in urwid
"""

from collections import MutableMapping
import itertools
from string import punctuation # pylint: disable=deprecated-module

import urwid


class IndexedMenuEnumerator(MutableMapping):
    """
    Generates new indexes for enumerating a menu and associates an index to
    a vselection.

    A selection is used by calling code to tell which entry was selected via
    a keypress
    """
    idx_names = [str(c) for c in itertools.chain(range(1, 9), [0], (c for c in punctuation if c not in frozenset('(){}[]<>')))]

    def __init__(self):
        self.association = {}
        self.idx = 0

    def set_next(self, selection):
        try:
            key = self.idx_names[self.idx]
        except IndexError:
            raise IndexError('Not enough prefixes to enumerate all list entries')
        self.idx += 1
        self.association[key] = selection
        return key

    def __setitem__(self, name, selection):
        self.association[name] = selection
        pass

    def __getitem__(self, name):
        return self.association[name]

    def __delitem__(self, name):
        del self.association[name]

    def __iter__(self):
        return iter(self.association)

    def __len__(self):
        return len(self.association)


class IndexedMenuButton(urwid.Button):
    """A button without decorations"""
    button_left = urwid.Text("")
    button_right = urwid.Text("")


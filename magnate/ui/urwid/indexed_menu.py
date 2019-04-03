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

from collections.abc import MutableMapping
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
    idx_names = [str(c) for c in itertools.chain(
        range(1, 10),
        [0],
        (c for c in punctuation if c not in frozenset('(){}[]<>'))
    )]

    def __init__(self):
        self.association = {}
        self.idx = 0

    def set_next(self, selection):
        """
        Adds a new selection to the IndexedMenuEnumerator, picking the new key
        from the list of valid enumerations

        :arg selection: The value being set
        :returns: The key that was picked
        """
        try:
            key = self.idx_names[self.idx]
        except IndexError:
            raise IndexError('Not enough prefixes to enumerate all list entries')
        self.idx += 1
        self.association[key] = selection
        return key

    def clear(self):
        """
        Clear the mapping

        In addition to normal dict behaviour, this also resets the next index back to the beginning
        """
        super().clear()
        self.idx = 0

    def __setitem__(self, name, selection):
        """Sets a key's value.

        :arg name: The key
        :arg selection: The value

        .. warning:: Unlike dict, this cannot be used to set new keys.  Use
            :meth:`set_next` instead.
        """
        if name not in self.association:
            raise KeyError('Can only create new keys for an IndexedMenuEnumerator via set_next()')
        self.association[name] = selection

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

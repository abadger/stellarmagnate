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


class TravelDisplay(urwid.ListBox):
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
            self.pubpen.publish('action.ship.movement_attempt', destination)
            return
        super().keypress(size, key)
        return key

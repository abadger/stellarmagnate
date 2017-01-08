# Stellar Magnate - A space-themed commodity trading game
# Copyright (C) 2016-2017 Toshio Kuratomi <toshio@fedoraproject.org>
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
Give a menu of new destinations for the ship to move to
"""
from functools import partial

import urwid

from .indexed_menu import IndexedMenuEnumerator, IndexedMenuButton
from .sideless_linebox import SidelessLineBox


class TravelDisplay(urwid.WidgetWrap):
    """Widget that allows the user to select a new destination for the ship"""
    _selectable = True
    signals = ['close_travel_menu']

    def __init__(self, pubpen):
        self.pubpen = pubpen
        self.keypress_map = IndexedMenuEnumerator()
        self._ship_moved_sub_id = None

        self.listwalker = urwid.SimpleFocusListWalker([])
        box = urwid.ListBox(self.listwalker)
        outer_layout = SidelessLineBox(box, lline=None, blcorner='─',
                                       tlcorner='─', trcorner='\u252c',
                                       brcorner='\u2524')
        super().__init__(outer_layout)
        self.pubpen.subscribe('ship.destinations', self.handle_new_destinations)

    # pubpen event handlers

    def handle_new_destinations(self, locations):
        """Update the destination list when the ship can move to new places"""
        self.listwalker.clear()
        self.keypress_map = IndexedMenuEnumerator()
        #for idx, location in enumerate(locations):
        for location in locations:
            prefix = self.keypress_map.set_next(location)
            button = IndexedMenuButton('({}) {}'.format(prefix, location))
            self.listwalker.append(urwid.AttrMap(button, None, focus_map='reversed'))
            urwid.connect_signal(button, 'click', partial(self.handle_button_click, location))

    def handle_new_location(self, *args):
        """Got a valid new location so we can close this window"""
        self.pubpen.unsubscribe(self._ship_moved_sub_id)
        self._ship_moved_sub_id = None
        urwid.emit_signal(self, 'close_travel_menu')

    # urwid event handlers

    def handle_button_click(self, location, *args):
        """Handle menu selection via button click"""
        if self._ship_moved_sub_id is None:
            self._ship_moved_sub_id = self.pubpen.subscribe('ship.moved', self.handle_new_location)
        self.pubpen.publish('action.ship.movement_attempt', location)

    def keypress(self, size, key):
        """Handle all keyboard shortcuts for the travel menu"""
        if key in self.keypress_map:
            destination = self.keypress_map[key]
            if self._ship_moved_sub_id is None:
                self._ship_moved_sub_id = self.pubpen.subscribe('ship.moved', self.handle_new_location)
            self.pubpen.publish('action.ship.movement_attempt', destination)
            return
        super().keypress(size, key)  #pylint: disable=not-callable
        return key

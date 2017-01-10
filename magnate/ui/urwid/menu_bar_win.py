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
Top level menubar that let's the player select the major game options
"""

import urwid


class MenuBarWindow(urwid.WidgetWrap):
    """Menu displaying major player options"""
    _selectable = True

    def __init__(self, pubpen):
        self.pubpen = pubpen

        self.exchange_entry = urwid.Text('(C)ommodity Exchange')
        self.port_entry = urwid.Text('(P)ort District')
        self.financial_entry = urwid.Text('(F)inancial')
        self.travel_entry = urwid.Text('(T)ravel')
        self.game_menu_entry = urwid.Text('(M)enu')

        self.menu_entries = urwid.Columns((
            ('weight', 1, urwid.Divider(' ')),
            (len('(C)ommodity Exchange') + 4, self.exchange_entry),
            (len('(P)ort District') + 4, self.port_entry),
            (len('(F)inancial') + 4, self.financial_entry),
            (len('(T)ravel') + 4, self.travel_entry),
            (len('(M)enu') + 4, self.game_menu_entry),
            ('weight', 1, urwid.Divider(' ')),
            ), dividechars=1)

        super().__init__(self.menu_entries)

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


class TitleCard(urwid.LineBox):
    """Display a splash screen"""
    signals = ['close_title_card']

    def __init__(self, pubpen):
        self.pubpen = pubpen

        program_name = urwid.Text('Stellar Magnate', align='center')
        copyright_name = urwid.Text('(C) 2016, Toshio Kuratomi', align='center')
        license = urwid.Text('GNU General Public License 3.0 or later', align='center')
        screen = urwid.Filler(urwid.Pile([program_name, copyright_name, license]), valign='middle')
        super().__init__(screen)

    def keypress(self, *args):
        urwid.emit_signal(self, 'close_title_card')

    def selectable(self):
        # Decoration widgets like LineBox override selectable() so we need to
        # use an actual method
        return True



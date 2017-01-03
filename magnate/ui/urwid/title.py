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
A splash screen for the Stellar Magnate Program
"""

import urwid

from ... import release

class TitleCard(urwid.LineBox):
    """Display a splash screen"""
    signals = ['close_title_card']

    def __init__(self, pubpen):
        self.pubpen = pubpen

        program_name = urwid.Text(release.PROGRAM_NAME, align='center')
        copyright_name = urwid.Text('© {}, {}'.format(release.COPYRIGHT_YEAR, release.AUTHOR), align='center')
        license_name = urwid.Text(release.LICENSE, align='center')

        screen = urwid.Filler(urwid.Pile([program_name, copyright_name, license_name]), valign='middle')
        super().__init__(screen)

    def keypress(self, *args):
        """Any interaction with the widget moves on to the next screen"""
        urwid.emit_signal(self, 'close_title_card')

    def selectable(self):
        """Allow the user to interact with this widget"""
        # Decoration widgets like LineBox override selectable() so we need to
        # use an actual method
        return True

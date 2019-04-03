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
Message window displays errors and events.
"""
from enum import Enum
from functools import partial

import urwid


MsgType = Enum('MsgType', ('info', 'error'))


class MessageWindow(urwid.WidgetWrap):
    """Display system messages"""
    _MAX_MESSAGES = 3
    _MIN_TIME_BETWEEN_MESSAGES = 0.7
    _can_print_message = True

    def __init__(self, pubpen):
        self.pubpen = pubpen
        self.loop = self.pubpen.loop

        self.message_list = urwid.SimpleFocusListWalker([])
        list_box = urwid.ListBox(self.message_list)
        message_win = urwid.LineBox(list_box, tline=None, lline=None, bline=None,
                                    trcorner='│', brcorner='│')
        super().__init__(message_win)
        self.pubpen.subscribe('user.login_failure', partial(self.add_message, severity=MsgType.error))
        self.pubpen.subscribe('user.order_failure', partial(self.add_message, severity=MsgType.error))
        self.pubpen.subscribe('ship.movement_failure', partial(self.add_message, severity=MsgType.error))
        self.pubpen.subscribe('market.event', self.handle_market_event)
        self.pubpen.subscribe('ui.urwid.message', self.add_message)

    @property
    def height(self):
        """How many rows the message window occupies"""
        return self._MAX_MESSAGES

    def handle_market_event(self, location, commodity, price, msg):
        """
        Format market event message.

        These are different as they can take place anywhere, not just in the
        location where the user is present.
        """
        self.add_message('NEWS from {}: {}'.format(location, msg))

    def add_message(self, msg, severity=MsgType.info):
        """
        Add a message to the MessageWindow.

        Reap older messages if there are too many
        """
        if not self._can_print_message:
            self.loop.call_later(self._MIN_TIME_BETWEEN_MESSAGES, self.add_message, msg, severity)
            return

        if severity is MsgType.error:
            msg = urwid.Text(('reversed', msg))
        else:
            msg = urwid.Text(msg)
        self.message_list.append(msg)
        while len(self.message_list) > self._MAX_MESSAGES:
            self.message_list.pop(0)

        self._can_print_message = False
        self.loop.call_later(self._MIN_TIME_BETWEEN_MESSAGES,
                             partial(setattr, self, '_can_print_message', True))

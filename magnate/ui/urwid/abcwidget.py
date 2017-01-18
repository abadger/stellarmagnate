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
A metaclass that combines urwid's widget metaclass with abstract base class

We need to define this to solve which base class can override the other.
"""

from abc import ABCMeta

import urwid


class ABCWidget(urwid.WidgetMeta, ABCMeta):
    """Combine ABCMeta and Widgetmeta together so that we can have a metaclass with both"""
    pass

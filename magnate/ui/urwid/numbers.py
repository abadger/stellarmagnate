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
"""Utility functions for dealing with numbers"""

import locale

def format_number(number, max_chars=7):
    """
    Format a number in a human readable form.  This adds locale-specific separators.

    If the number is too long, se scientific notation.

    :kwarg max_chars: The maximum number of characters a number can take on
        the screen before it is turned into scientific notation.
    """
    formatted_number = locale.format('%d', number, grouping=True)
    if len(formatted_number) > max_chars:
        formatted_number = '{:.1E}'.format(number)

    return formatted_number

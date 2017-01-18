# Stellar Magnate - A space-themed commodity trading game
# Copyright (C) 2017 Toshio Kuratomi <toshio@fedoraproject.org>
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
All exceptions raised by the core engine
"""
class MagnateError(Exception):
    """Base of the Magnate exception hierarchy"""
    pass

class MagnateConfigError(MagnateError):
    """Raised when processing config files"""
    pass

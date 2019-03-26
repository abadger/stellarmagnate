# Stellar Magnate - A space-themed commodity trading game
# Copyright (C) 2019 Toshio Kuratomi <toshio@fedoraproject.org>
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
Dispatchers handle all of the core-side callbacks that respond to events.

These are light wrappers that call the objcets which do the real work.  This way all the callbacks
are here for ease of discovery but the work is performed by objects which also interact with the data.
"""
import straight.plugin

from __main__ import magnate


def register_event_handlers():
    """Register event handlers"""
    dispatchers = straight.plugin.load('magnate.dispatchers')
    for module in dispatchers:
        module.register_event_handlers(magnate.pubpen)

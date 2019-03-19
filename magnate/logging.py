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
:mod:`logging` holds a twiggy Logger object which controls logging for the application
"""

import twiggy


# Temporarily setup twiggy logging with defaults until we can get real configuration.
twiggy.quick_setup()

#: The magnate log.  For the stellar magnate client, the name of the logger is #:
#: `stellarmagnate.magnate`.  For those used to the idiom of using the module's __name__ field as
#: the name, the module name is in the `mod` field.
log = twiggy.log.name('stellarmagnate.magnate')

mlog = log.fields(mod=__name__)
mlog.debug('logging loaded')

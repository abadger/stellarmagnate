# Stellar Magnate - A space-themed commodity trading game
# Copyright (C) 2018 Toshio Kuratomi <toshio@fedoraproject.org>
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
Routines to load base game types from data files
"""
import enum
import os

import twiggy
from voluptuous import Schema, Required
from voluptuous.humanize import validate_with_humanized_errors

try:  # pragma: no cover
    from yaml import CSafeLoader as Loader
except ImportError:  # pragma: no cover
    from yaml import SafeLoader as Loader


# Enums that are created at runtime and then used with the database.  See the
# data/base/stellar-types.yml file if you suspect this list is out of date
# * CommodityType
# * LocationType
# * OrderStatusType


def type_name(value):
    """Validate that the names of types follow our conventions"""
    if not isinstance(value, str):
        raise ValueError('Type names must be strings')
    if not value.endswith('Type'):
        raise ValueError('Type names must end with "Type"')
    if not value[0] == value[0].upper():
        raise ValueError('Type names must begin with an uppercase character (following class'
                         ' naming conventions)')
    return value


DATA_TYPES_SCHEMA = Schema({
    Required('types'): {
        type_name: [str]
    },
    })


def load_base_types(datadir):
    """
    Parse the yaml file of base enum types and return the information

    :arg datadir: The data directory to find the types file
    :returns: A list of types
    """
    flog = twiggy.log.name('savegame types').fields(function='load_base_types')
    flog.debug('Entered function')

    data_file = os.path.join(datadir, 'base', 'stellar-types.yml')

    flog = flog.fields(filename=data_file)
    flog.debug('data_file path constructed')

    flog.debug('Opening data_file')
    with open(data_file, 'r') as data_fh:
        flog.debug('reading data_file')
        yaml_data = data_fh.read()
        flog.fields(yaml=yaml_data).debug('parsing yaml string')
        loader = Loader(yaml_data)
        data = loader.get_single_data()

    flog.fields(data=data).debug('Validating type data structure')
    validate_with_humanized_errors(data, DATA_TYPES_SCHEMA)

    flog.debug('Done.  Returning data')
    return data


def init_base_types(datadir):
    """
    Initialize the global base types from the types data file

    :arg datadir: The data directory to find the types file

    **Side effects**: This function initializes the global Type variables which are Python Enums for
    various data types (Types of Commodities, Types of Locations, etc).  Since it modifies module
    globals it needs to be run early, before any threading.  The Type variables are used by
    everything else in savegames so it should be run as one of the first things upon accessing
    a savegame.
    """
    base_type_data = load_base_types(datadir)

    m_globals = globals()
    for name, entries in base_type_data['types'].items():
        m_globals[name] = enum.Enum(name, entries, module=__name__)

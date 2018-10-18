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
Routines to load base game data from yaml files
"""
import os
# string is not deprecated, only some methods within it. pylint is wrong
import string  # pylint: disable=deprecated-module

import voluptuous as v
from voluptuous.humanize import validate_with_humanized_errors as v_validate

try:  # pragma: no cover
    from yaml import CSafeLoader as Loader
except ImportError:  # pragma: no cover
    from yaml import SafeLoader as Loader

from . import base_types


BASE_SCHEMA = None
SYSTEM_SCHEMA = None


def known_celestial(data):
    """Ensures that any celestial mentioned in a location is present in the stellar system"""
    for system in data['systems']:
        celestials = {c['name'] for c in system['celestials']}
        for location in system['locations']:
            if location['celestial'] not in celestials:
                raise v.error.Invalid('locations must belong to a known celestial,'
                                      ' not {}'.format(location['celestial']))
    return data


def volume_or_storage(data):
    """Ensures that all ship parts either take up room or add storage space"""
    for part in data['ship_parts']:
        if ((part['volume'] is None and part['storage'] is None) or
                (part['volume'] is not None and part['storage'] is not None)):
            raise v.error.Invalid('ship_part {} must either take up room or'
                                  ' add room'.format(part['name']))
    return data


def _define_schemas(datadir):
    """
    Define the data file schemas

    We do this in a function instead of at the toplevel because the Types in base_types are dynamic.
    Therefore, base_types.init_base_types has to have run prior to defining the schema.
    """

    base_types.init_base_types(datadir)

    global BASE_SCHEMA, SYSTEM_SCHEMA

    system_structure = v.Schema({'version': '0.1',
                                 'systems': [{
                                     'name': v.All(str, string.capwords),
                                     'celestials': [{
                                         'name': v.All(str, string.capwords),
                                         'orbit': int,
                                         'type': base_types.CelestialType.validator,
                                         }],
                                     'locations': [{
                                         'name': v.All(str, string.capwords),
                                         'type': base_types.LocationType.validator,
                                         'celestial': str,
                                         }],
                                     'commodities': [{
                                         'name': v.All(str, string.capwords),
                                         'categories': [base_types.CommodityType.validator],
                                         'mean_price': int,
                                         'standard_deviation': int,
                                         # tenths of a percent
                                         'depreciation_rate': int,
                                         'volume': int,
                                         }],
                                     }], },
                                required=True)

    SYSTEM_SCHEMA = v.Schema(v.All(system_structure,
                                   known_celestial))

    base_structure = v.Schema({'version': '0.1',
                               'ships': [{
                                   'name': v.All(str, string.capwords),
                                   'mean_price': int,
                                   'standard_deviation': int,
                                   'depreciation_rate': int,
                                   'storage': int,
                                   'weapon_mounts': int,
                                   }],
                               'property': [{
                                   'name': v.All(str, string.capwords),
                                   'mean_price': int,
                                   'standard_deviation': int,
                                   'depreciation_rate': int,
                                   'storage': int,
                                   }],
                               'ship_parts': [{
                                   'name': v.All(str, string.capwords),
                                   'mean_price': int,
                                   'standard_deviation': int,
                                   'depreciation_rate': int,
                                   v.Optional('volume', default=None): v.Any(None, int),
                                   v.Optional('storage', default=None): v.Any(None, int),
                                   }],
                               'events': [{
                                   'msg': str,
                                   'adjustment': int,
                                   'affects': [v.Any(base_types.CommodityType.validator,
                                                     [base_types.CommodityType.validator])],
                                   }], },
                              required=True)

    BASE_SCHEMA = v.Schema(v.All(base_structure,
                                 volume_or_storage))


def load_data_definitions(datadir):
    """
    Parse the yaml file of base yaml objects and return the information

    :arg file yaml_file: Open file object to read the yaml from
    :returns: An array of Markets that the user can travel to.
    """
    _define_schemas(datadir)

    data_file = os.path.join(datadir, 'base', 'stellar-base.yml')

    with open(data_file) as f:
        loader = Loader(f.read())
        base_data = loader.get_single_data()
    v_validate(base_data, BASE_SCHEMA)

    data_file = os.path.join(datadir, 'base', 'stellar-sol.yml')
    with open(data_file) as f:
        loader = Loader(f.read())
        system_data = loader.get_single_data()
    v_validate(system_data, SYSTEM_SCHEMA)

    base_data.update(system_data)
    del base_data['version']

    return base_data

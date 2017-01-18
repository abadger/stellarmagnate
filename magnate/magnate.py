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
:class:`Magnate` is in ultimate charge of the whole game
"""

import argparse
import asyncio
import json
import os
import sys
from collections import OrderedDict

import jsonschema
from pubmarine import PubPen
from straight.plugin import load

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

from .config import read_config
from .dispatcher import Dispatcher
from .market import CommodityData, LocationData, SystemData
from .market import Commodity, Market
from .release import __version__
from .ship import ShipData, Ship
from .ui.api import UserInterface
#from .user import User


class User:
    """A logged in user"""
    def __init__(self, pubpen, username):
        self.pubpen = pubpen
        self.username = username
        self._cash = 500
        self.ship = None

        self.pubpen.subscribe('query.user.info', self.handle_user_info)

    def handle_user_info(self):
        """Return all information about a user

        :event user.info: All the information about the user
        """
        self.pubpen.publish('user.info', self.username, self.cash,
                            self.ship.location.name)

    @property
    def cash(self):
        """Property for retrieving user's cash"""
        return self._cash

    @cash.setter
    def cash(self, new_cash):
        """
        Prevent user's cash from going below zero

        :event user.cash.update: Publish when the user's cash changes.
        """
        if not isinstance(new_cash, int) or new_cash < 0:
            raise ValueError('Invalid value of cash: {}'.format(new_cash))

        old_cash = self._cash
        self._cash = new_cash
        self.pubpen.publish('user.cash.update', new_cash, old_cash)


def _parse_args(args=tuple(sys.argv)):
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='A space themed trading game')
    parser.add_argument('--version', action='version', version=__version__)
    parser.add_argument('--conf-file', dest='cfg_file', action='store', default=None,
                        help='Alternate location for configuration file')
    parser.add_argument('--_testing-configuration', dest='test_cfg', action='store_true',
                        help='Overrides data file locations for running from a source checkout.'
                             ' For development only')

    ui_plugin_names = []
    ui_plugins = load('magnate.ui', subclasses=UserInterface)
    for plugin in ui_plugins:
        ui_plugin_names.append(plugin.__module__[len('magnate.ui.'):])

    parser.add_argument('--ui-plugin', dest='ui_plugin', action='store', default=None,
                        help='Specify a user interface plugin to use.'
                             ' Valid plugin names: {}'.format(', '.join(ui_plugin_names)))

    return parser.parse_args(args[1:])


class Magnate:
    """
    The main Magnate client class

    This handles initializing and setting up the game client.
    """
    def __init__(self):
        # Parse command line arguments
        args = _parse_args(sys.argv)

        # Read configuration in
        conf_args = []
        if args.cfg_file:
            conf_args.append(args.cfg_file)
        self.cfg = read_config(conf_args, testing=args.test_cfg)

        # Override config options with command line options
        if args.ui_plugin:
            self.cfg = args.ui_plugin

        #
        # Attributes
        #
        self.pubpen = None
        self.dispatcher = None

        # Base data attributes
        self._load_data_definitions()

        # Instantiated attributes
        self.user = None
        self.equipment = None
        self.markets = None

    def _load_data_definitions(self):
        """
        Parse the yaml file of base yaml objects and return the information

        :arg file yaml_file: Open file object to read the yaml from
        :returns: An array of Markets that the user can travel to.
        """
        data_file = os.path.join(self.cfg['base_data_dir'], 'stellar.yml')
        schema_file = os.path.join(self.cfg['schema_dir'], 'stellar-schema.json')

        loader = Loader(open(data_file).read())
        data = loader.get_single_data()

        schema = json.loads(open(schema_file).read())
        jsonschema.validate(data, schema)

        self.system_data = OrderedDict()
        for system in data['system']:
            self.system_data[system['name']] = SystemData(system['name'], None)

            locations = OrderedDict()
            for loc in system['location']:
                locations[loc['name']] = LocationData(loc['name'], loc['type'], self.system_data[system['name']])
            self.system_data[system['name']].locations = locations

        # Commodities are anything that may be bought or sold at a particular
        # location.  The UI may separate these out into separate pieces.
        commodities = OrderedDict()
        for commodity in data['cargo']:
            commodities[commodity['name']] = CommodityData(commodity['name'],
                                                           frozenset((commodity['type'], 'cargo')),
                                                           commodity['mean_price'],
                                                           commodity['standard_deviation'],
                                                           commodity['depreciation_rate'],
                                                           1,
                                                           commodity['event'],
                                                          )

        for commodity in data['equipment']:
            commodities[commodity['name']] = CommodityData(commodity['name'],
                                                           frozenset((commodity['type'], 'equipment')),
                                                           commodity['mean_price'],
                                                           commodity['standard_deviation'],
                                                           commodity['depreciation_rate'],
                                                           commodity['holdspace'],
                                                           commodity['event'],
                                                          )

        for commodity in data['property']:
            commodities[commodity['name']] = CommodityData(commodity['name'],
                                                           frozenset(('property',)),
                                                           commodity['mean_price'],
                                                           commodity['standard_deviation'],
                                                           commodity['depreciation_rate'],
                                                           0,
                                                           commodity['event'],
                                                          )
        self.commodity_data = commodities

        ### FIXME: Put ships into commodities too.
        ships = OrderedDict()
        for ship in data['ship']:
            ships[ship['name']] = ShipData(ship['name'], ship['mean_price'],
                                           ship['standard_deviation'],
                                           ship['depreciation_rate'],
                                           ship['holdspace'],
                                           ship['weaponmount'])
        self.ship_data = ships

    def _load_save(self):
        """Load a save file"""
        ### FIXME: Need to load game from save file
        pass

    def _setup_markets(self):
        """Setup the stateful bits of markets"""
        self.markets = OrderedDict()
        ### FIXME: Eventually need to handle other systems besides Sol
        for loc in self.system_data['Sol'].locations.values():
            commodities = OrderedDict((c.name, Commodity(self.pubpen, c)) for c in self.commodity_data.values())
            market = Market(self, loc, commodities)
            self.markets[loc.name] = market

    def create_ship(self, ship_type, location):
        """
        Create a new instance of a ship type

        :arg ship_type: The class name of the ship to create
        :return: a new :class:`magnate.ship.Ship`
        """
        return Ship(self, self.ship_data[ship_type], self.markets[location])

    def login(self, username, password):
        """Log a user into the game"""

        if 'toshio' in username.lower():
            # Game can begin in earnest now
            self.user = User(self.pubpen, username)
            self.user.ship = self.create_ship('Passenger', 'Earth')

            self.pubpen.publish('user.login_success', username)
            return self.user
        else:
            self.pubpen.publish('user.login_failure',
                                'Unknown account: {}'.format(username))

    def run(self):
        """
        Run the program.  This is the main entrypoint to the magnate client
        """
        ui_plugins = load('magnate.ui', subclasses=UserInterface)
        for UIClass in ui_plugins:  #pylint: disable=invalid-name
            if UIClass.__module__.startswith('magnate.ui.{}'.format(self.cfg['ui_plugin'])):
                break
        else:
            print('Unknown user ui: {}'.format(self.cfg['ui_plugin']))
            return 1

        loop = asyncio.get_event_loop()
        self.pubpen = PubPen(loop)
        self._setup_markets()
        self.dispatcher = Dispatcher(self, self.markets)

        # UIClass is always available because we'd have already returned (via
        # the for-else) if UIClass was not defined
        user_interface = UIClass(self.pubpen) #pylint: disable=undefined-loop-variable

        return user_interface.run()

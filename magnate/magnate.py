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
        self.cash = 500
        self.ship = None

        self.pubpen.subscribe('query.user.info', self.handle_user_info)

    def handle_user_info(self):
        """Return all information about a user

        :event user.info: All the information about the user
        """
        self.pubpen.publish('user.info', self.username, self.cash,
                            self.ship.location)


class Magnate:
    """
    The main Magnate client class

    This handles initializing and setting up the game client.
    """
    def __init__(self):
        # Parse command line arguments
        args = self._parse_args(sys.argv)

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

    def _parse_args(self, args=sys.argv):
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

        commodities = OrderedDict()
        for commodity in data['commodity']:
            commodities[commodity['name']] = CommodityData(commodity['name'],
                                                           commodity['type'],
                                                           commodity['mean_price'],
                                                           commodity['standard_deviation'],
                                                           commodity['depreciation_rate'],
                                                           commodity['event'],
                                                          )
        self.commodity_data = commodities

        ### FIXME: These need to be worked out
        self.equipment_data = data['equipment']
        self.property_data = data['property']

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
        for loc in self.system_data['Sol'].locations.values():
            commodities = OrderedDict((c.name, Commodity(self.pubpen, c)) for c in self.commodity_data.values())
            market = Market(self.pubpen, loc, commodities)
            self.markets[loc.name] = market

    def create_ship(self, ship_type):
        """
        Create a new instance of a ship type

        :arg ship_type: The class name of the ship to create
        :return: a new :class:`magnate.ship.Ship`
        """
        return Ship(self.pubpen, self.ship_data[ship_type])

    def login(self, username, password):
        """Log a user into the game"""
        if 'toshio' in username.lower():
            self.pubpen.publish('user.login_success', username)

            # Game can begin in earnest now
            self.user = User(self.pubpen, username)
            self.user.ship = self.create_ship('Passenger')
            return self.user
        else:
            self.pubpen.publish('user.login_failure',
                                'Unknown account: {}'.format(username))
#    def login(self, username, password):
#        """Log a user into the game"""
#        if 'toshio' in username.lower():
#            self.pubpen.publish('user.login_success', username)
#            # Game can begin in earnest now
#            self.markets, self.ship_list = load_data_definition(self.pubpen, 'stellar.yml')
#
#            ### FIXME: In the future a ship should know what location it is
#            # at.  And then it should be able to lookup what locations it can
#            # reach from that planet.
#            global ALL_DESTINATIONS
#            ALL_DESTINATIONS = tuple(m for m in self.markets)
#            self.user = User(self.pubpen, username)
#            self.user.ship = Ship(self.pubpen, self.ship_list['Passenger'])
#        else:
#            self.pubpen.publish('user.login_failure',
#                                'Unknown account: {}'.format(username))


    def run(self):
        """
        Run the program.  This is the main entrypoint to the magnate client
        """
        ui_plugins = load('magnate.ui', subclasses=UserInterface)
        for UIClass in ui_plugins:
            if UIClass.__module__.startswith('magnate.ui.{}'.format(self.cfg['ui_plugin'])):
                break
        else:
            print('Unknown user ui: {}'.format(self.cfg['ui_plugin']))
            return 1

        loop = asyncio.get_event_loop()
        self.pubpen = PubPen(loop)
        self._setup_markets()
        self.dispatcher = Dispatcher(self.pubpen, self, self.markets)

        ui = UIClass(self.pubpen)

        return ui.run()

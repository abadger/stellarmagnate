# Stellar Magnate - A space-themed commodity trading game
# Copyright (C) 2016-2019 Toshio Kuratomi <toshio@fedoraproject.org>
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
import glob
import os
import os.path
import sys
from collections import OrderedDict

import twiggy
from pubmarine import PubPen
from straight.plugin import load

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

from .auth import AccountDB
from .config import read_config
from .errors import MagnateAuthError
from .logging import log
from .market import Commodity, CommodityData, LocationData, Market, SystemData
from .player import Player
from .release import __version__
from .ship import ShipData, Ship
from .ui.api import UserInterface


mlog = log.fields(mod=__name__)


def _parse_args(args=tuple(sys.argv)):
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='A space themed trading game')
    parser.add_argument('--version', action='version', version=__version__)
    parser.add_argument('--conf-file', dest='cfg_file', action='store', default=None,
                        help='Alternate location for configuration file')
    parser.add_argument('--ui-args', dest='ui_args', action='append', default=[],
                        help='Extra arguments for the user interface plugins. Only needed if the'
                        ' arguments conflict with stellar magnate arguments.  Specify this for each extra arg')
    parser.add_argument('--use-uvloop', dest='uvloop', action='store_true', default=False,
                        help='Enable use of uvloop instead of the default asyncio event loop.')
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

    args, remainder = parser.parse_known_args(args[1:])

    # Extra arguments for the ui plugins
    remainder.extend(args.ui_args)
    args.ui_args = remainder

    return args


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
        if args.uvloop:
            self.cfg['use_uvloop'] = True

        if args.ui_plugin:
            self.cfg['ui_plugin'] = args.ui_plugin

        self.cfg['ui_args'] = args.ui_args

        #
        # Attributes
        #
        self.pubpen = None

        # Instantiated attributes
        self.accounts_db = None
        self.user = None

    def _load_save(self):
        """Load a save file"""
        ### FIXME: Need to load game from save file
        pass

    def login(self, username, password):
        """
        Log a user into the game

        :raises MagnateAuthError: if the username or password are incorrect
        """
        if self.accounts_db.authenticate(username, password):
            self.user = username
        else:
            raise MagnateAuthError(f'Incorrect credentials for {username}')

    def create_user(self, username, password):
        """Create a new user account"""
        self.accounts_db.create_account(username, password)

    def run(self):
        """
        Run the program.  This is the main entrypoint to the magnate client
        """
        flog = mlog.fields(func='Magnate.run')

        # Create the statedir if it doesn't exist
        if not os.path.exists(self.cfg['state_dir']):
            os.makedirs(self.cfg['state_dir'])

        # Reconfigure logging now that we have a state_dir where any log files will land in the
        # default config
        twiggy.dict_config(self.cfg['logging'])

        auth_dir = os.path.join(self.cfg['state_dir'], 'auth')
        if not os.path.exists(auth_dir):
            os.makedirs(auth_dir)
        self.accounts_db = AccountDB(os.path.join(auth_dir, 'authn.dbm'),
                                     self.cfg['authentication']['passlib'])

        ui_plugins = load('magnate.ui', subclasses=UserInterface)
        for UIClass in ui_plugins:  # pylint: disable=invalid-name
            if UIClass.__module__.startswith('magnate.ui.{}'.format(self.cfg['ui_plugin'])):
                break
        else:
            flog.error('Unknown user ui: {}', self.cfg['ui_plugin'])
            return 1

        # Try using uvloop instead of the asyncio event loop
        if self.cfg['use_uvloop']:
            try:
                import uvloop
            except Exception as e:
                flog.warning('Could not import uvloop.  Falling back on asyncio event'
                             ' loop: {}', str(e))
            else:
                try:
                    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
                except Exception as e:
                    flog.warning('Could not set uvloop to be the event loop.  Falling back on'
                                 ' asyncio event loop: {}', str(e))

        loop = asyncio.get_event_loop()
        self.pubpen = PubPen(loop)

        #
        # Callbacks
        #

        # Import of dispatcher has to be done after __init__() because it references
        # __main__.magnate
        from . import dispatcher

        # Have dispatchers register to handle events
        dispatcher.register_event_handlers()

        self.pubpen.subscribe('query.game.list_save_games', self.handle_list_save_games)

        # UIClass is always available because we'd have already returned (via
        # the for-else) if UIClass was not defined
        try:
            user_interface = UIClass(self.pubpen, self.cfg['ui_args'])  # pylint: disable=undefined-loop-variable
            flog.info('Starting user interface {}', self.cfg['ui_plugin'])
            return user_interface.run()
        except Exception as e:
            flog.trace('error').error(f'Exception raised while running the user interface: {e}')
            raise

    ### FIXME: These go away.  Either moved or replaced by the savegame
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

    def handle_list_save_games(self):
        """List the save games"""
        savegames = []
        for filename in glob.glob(os.path.join(self.cfg['state_dir'], '*.smg')):
            savegames.append(savegame.load.savegame_info(filename))
        self.pubpen.publish('game.')

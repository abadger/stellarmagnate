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
The dataloader module loads information from yaml files and saves it into
data structures for the rest of the program.

There are several types of yaml file:

    :data definitions: Set base information.  This is information that never
        changes such as names of locations, range of prices for commodities, etc.
    :save file: Show an evolution of the base definition.  This includes
        things like current prices, a user's cash, etc.

    The data definition includes names of commodities and their price ranges.
    The save file saves the current price and time offset.
"""

import copy
import datetime
import json
import os
from collections import OrderedDict

import jsonschema
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

from .market import CommodityData, LocationData
from .market import Commodity, Market
from .user import Ship, User

# Need to make this configurable
DATADIR = os.path.normpath(os.path.join(os.path.dirname(__file__), '../data/'))


# Load base data
def load_data_definition(pubpen, yaml_file):
    """
    Parse the yaml file of base yaml objects and return the information

    :arg file yaml_file: Open file object to read the yaml from
    :returns: An array of Markets that the user can travel to.
    """
    loader = Loader(open(os.path.join(DATADIR, yaml_file)).read())
    data = loader.get_single_data()
    schema = json.loads(open(os.path.join(DATADIR, 'stellar-schema.json')).read())
    jsonschema.validate(data, schema)

    commodity_data = []
    for entry in data['market']:
        commodity = CommodityData(entry['name'], entry['type'], entry['mean_price'], entry['standard_deviation'], entry['depreciation_rate'], entry['events'])
        commodity_data.append(commodity)

    markets = OrderedDict()
    for location in data['system']['locations']:
        loc = LocationData(location['name'], location['type'])
        commodities = OrderedDict((c.name, Commodity(pubpen, c)) for c in commodity_data)
        market = Market(pubpen, loc, commodities)
        markets[loc.name] = market

    return markets


# Load from save file
def load_state(pubpen, username, password, save_file=None):

    if save_file is None:
        # First, load default data definitions from file
        # Then Assign meaning to the data
        #
        # load list of ships, list of commodities, list of markets.
        #
        # Create a list of ShipData(), list of CommodityData(), list of LocationData()
        #   These instances are bases of data.
        #   Then create an instance of Ship() which hasa type of ShipData().
        #   a set of Commodities that each hasa type of CommodityData()
        #   the list of Locations() each has a LocationData() and list of
        #   Commodities
        # Create an instance of ShipDispatcher() that is owned by a User()
        # Create an instance of each LocationDispatcher() that is the owner of
        # Commodities().
        ship = Ship(pubpen)
        user = User(pubpen, username=username, cash=500, ship=ship)
        locations = load_data_definition(os.path.join(DATADIR, 'stellar.yml'))
    else:
        # Saved game
        pass
    return locations, user

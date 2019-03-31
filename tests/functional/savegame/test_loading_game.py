import builtins
import os.path
import re
from unittest.mock import mock_open, patch

import pytest

from magnate.savegame import db
from magnate.savegame import load
from magnate.savegame import data_def
from magnate.savegame import base_types


pytestmark = pytest.mark.usefixtures('clean_context')


LOADED_DATA = {
    'systems': [{'celestials': [{'name': 'Primary', 'orbit': 0, 'type': 'star'},
                                {'name': 'Friesland',
                                 'orbit': 1,
                                 'type': 'oxygen'}],
                 'commodities': [{'categories': ['chemical', 'illegal'],
                                  'depreciation_rate': 3,
                                  'mean_price': 1,
                                  'name': 'Drugs',
                                  'standard_deviation': 2,
                                  'volume': 4}],
                 'locations': [{'celestial': 'Primary',
                                'name': 'Solar Observation Station',
                                'type': 'orbital'}],
                 'name': 'Test'}],
    'property': [{'depreciation_rate': 3,
                  'mean_price': 1,
                  'name': 'property',
                  'standard_deviation': 2,
                  'storage': 4}],
    'ship_parts': [{'depreciation_rate': 12,
                    'mean_price': 10,
                    'name': 'add storage',
                    'standard_deviation': 11,
                    'storage': 13},
                   {'depreciation_rate': 22,
                    'mean_price': 20,
                    'name': 'take up space',
                    'standard_deviation': 21,
                    'volume': 23}],
    'ships': [{'depreciation_rate': 1,
               'mean_price': 10,
               'name': 'ship',
               'standard_deviation': 1,
               'storage': 0,
               'weapon_mounts': 1}],
    'events': [{'adjustment': -5,
                'affects': ['food', ['illegal', 'chemical']],
                'msg': 'price lower'},
               {'adjustment': 5,
                'affects': [['illegal', 'chemical'], 'food'],
                'msg': 'price higher'}],
}


def test_load_data_definitions(fake_datadir):
    base_data = data_def.load_data_definitions(fake_datadir)

    print(base_data)
    assert base_data == LOADED_DATA


def test_init_game(tmpdir, fake_datadir):
    """Test that init_game can create and load games"""

    savegame = os.path.join(tmpdir, 'test_game.sqlite')
    game_state = load.init_game(savegame, fake_datadir)

    assert game_state
    assert db.engine is game_state

    # Test that loading a second game loads the same file but creates a new engine
    game_state2 = load.init_game(savegame, fake_datadir)

    assert game_state2
    assert db.engine is game_state2
    assert game_state != game_state2

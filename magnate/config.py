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
Functions to read configuration files
"""

import itertools
import os.path

from configobj import ConfigObj
from kitchen.iterutils import iterate


SYSTEM_CONFIG_FILE = '/etc/stellarmagnate/magnate.cfg'
USER_CONFIG_FILE = os.path.expanduser('~/.stellarmagnate/magnate.cfg')

DEFAULT_CONFIG = """
# Directory in which the base data lives.  Commodity names and price ranges,
# Ship types, Locations, and such.
base_data_dir = {data_dir}/base

# Directory with schema that explains the structure of the data files
schema_dir = {data_dir}/schemas

# Directory to save games in
save_dir = ~/.stellarmagnate/saves

# name of the User Interface plugin to use
ui_plugin = urwid
""".format(data_dir='/usr/share/stellarmagnate',).split('\n')

TESTING_CONFIG = """
base_data_dir = {0}
schema_dir = {0}
""".format(os.path.join(os.path.dirname(__file__), '..', 'data')).split('\n')

CONFIG_SPEC = """
base_data_dir = string()
schema_dir = string()
save_dir = string()
ui_plugin = string()
""".split('\n')


def _find_config(conf_files=tuple()):
    """
    Return a list of config files that actually exist on the filesystem.

    :arg config_file: Manually specified config_file
    :returns: a list of config_files.  Configuration in the last files in the
        list should override the first ones.
    """
    paths = itertools.chain((SYSTEM_CONFIG_FILE, USER_CONFIG_FILE),
                            (os.path.expanduser(os.path.expandvars(p)) for p in iterate(conf_files)))

    config_files = []
    for conf_path in paths:
        if os.path.exists(conf_path):
            config_files.append(conf_path)

    return config_files


def _read_config(paths, testing=False):
    """
    Read the config files listed in path and merge them into a dictionary.

    :arg paths: filenames to read and merge configuration data from.  The last
        files should override the first ones.
    :arg testing: If set to True, then use paths to data files that are
        appropriate for testing a source checkout.
    :rtype: ConfigObj, a dict-like object with helper methods for use as a config store
    :returns: Return the configuration dict
    """
    cfg = ConfigObj(DEFAULT_CONFIG, configspec=CONFIG_SPEC)

    for cfg_file in paths:
        new_cfg = ConfigObj(cfg_file, configspec=CONFIG_SPEC)
        cfg.merge(new_cfg)

    if testing:
        testing_cfg = ConfigObj(TESTING_CONFIG, configspec=CONFIG_SPEC)
        cfg.merge(testing_cfg)

    return cfg


def read_config(conf_files=tuple(), testing=False):
    """
    Read configuration files

    :arg conf_files: filenames to read and merge configuration data from.  The last
        files should override the first ones.  A default set of config files
        in the systemwide conf dir  and the user's home directory are always included.
    :arg testing: If set to True, then use paths to data files that are
        appropriate for testing a source checkout.
    :rtype: ConfigObj, a dict-like object with helper methods for use as a config store
    :returns: Return the configuration dict
    """
    cfg_paths = _find_config(conf_files)
    return _read_config(cfg_paths, testing)

def write_default_config(filename):
    """
    Write out a default config file appropriate for a user to customize.

    :arg filename: The file path to write the config to.
    """
    cfg = ConfigObj(DEFAULT_CONFIG, configspec=CONFIG_SPEC)
    cfg.filename = filename
    cfg.write()

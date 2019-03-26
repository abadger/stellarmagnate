# Stellar Magnate - A space-themed commodity trading game
# Copyright (C) 2016-2017, Toshio Kuratomi <toshio@fedoraproject.org>
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
from collections.abc import MutableMapping

import yaml
from kitchen.iterutils import iterate
from voluptuous import All, Length, Schema, MultipleInvalid

from .errors import MagnateConfigError
from .logging import log


mlog = log.fields(mod=__name__)

STATE_DIR = os.path.expanduser('~/.stellarmagnate')
USER_DIR = os.path.expanduser('~/.stellarmagnate')

SYSTEM_CONFIG_FILE = '/etc/stellarmagnate/magnate.cfg'
USER_CONFIG_FILE = os.path.join(STATE_DIR, 'magnate.cfg')

LOG_FILE = os.path.join(STATE_DIR, 'magnate.log')


DEFAULT_CONFIG = """
# Directory in which the game data lives.  The data is further divided into subdirectories herein:
# base/   Commodity names and price ranges, ship types, locations, and such.
# schema/ schema for the data files in base *deprecated*, moving to voluptuous
# assets/ Images and other binary files
data_dir: {data_dir}/base

# Game state dir
# Saves, logs, and other data that changes during operation are saved as subdirs of this
state_dir: {state_dir}

# Name of the User Interface plugin to use
ui_plugin: urwid

# Whether to use uvloop instead of the stdlib asyncio event loop
use_uvloop: False

# Configuration of logging output.  This is given directly to twiggy.dict_cnfig()
logging:
  version: "1.0"
  outputs:
    logfile:
      output: twiggy.outputs.FileOutput
      args:
        - {log_file}
  emitters:
    all:
      level: WARNING
      output_name: logfile
      filters: []

authentication:
    # Configuration of authentication.  This is given directly to passlib
    # See the passlib documentation for details:
    # https://passlib.readthedocs.io/en/stable/narr/context-tutorial.html#loading-saving-a-cryptcontext
    passlib:
        schemes: ["pbkdf2_sha512", "sha512_crypt", "bcrypt", "argon2"]
        deprecated: []

""".format(data_dir='/usr/share/stellarmagnate', log_file=LOG_FILE, state_dir=STATE_DIR)

TESTING_CONFIG = """
data_dir: {base_dir}
logging:
  version: "1.0"
  outputs:
    logfile:
      output: twiggy.outputs.FileOutput
      args:
        - {log_file}
  emitters:
    all:
      level: DEBUG
      output_name: logfile
""".format(base_dir=os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'data')),
           log_file=LOG_FILE)

CONFIG_SCHEMA = Schema({
    'data_dir': All(str, Length(min=1)),
    'state_dir': All(str, Length(min=1)),
    'ui_plugin': All(str, Length(min=1, max=128)),
    'use_uvloop': bool,
    # The logging param is passed directly to twiggy.dict_config() which does its own validation
    'logging': dict,
    # The authentication param is passed directly to passlib which does its own validation
    'authentication': dict,
}, required=False)


def _find_config(conf_files=tuple()):
    """
    Return a list of config files that actually exist on the filesystem.

    :arg config_file: Manually specified config_file
    :returns: a list of config_files.  Configuration in the last files in the
        list should override the first ones.
    """
    flog = mlog.fields(func='_find_config')
    flog.fields(conf_files=conf_files).debug('Entered _find_config()')

    paths = itertools.chain((SYSTEM_CONFIG_FILE, USER_CONFIG_FILE),
                            (os.path.expanduser(os.path.expandvars(p)) for
                             p in iterate(conf_files)))

    config_files = []
    for conf_path in paths:
        if os.path.exists(conf_path):
            config_files.append(conf_path)

    flog.fields(cfg_files=config_files).debug('Leaving _find_config()')
    return config_files


def _merge_mapping(merge_to, merge_from, inplace=False):
    """
    Recurse through a dictionary's values merging new keys with old ones

    This is an in-place merge.

    :arg merge_to: dictionary to merge into
    :arg merge_from: dictionary to merge from
    :kwarg inplace: If True, merge_to will be modified directly.  If False, a copy of merge_to will
        be modified.
    :returns: the combined dictionary.  If inplace is True, then this is the same as merge_to after
        calling this function
    """
    flog = mlog.fields(func='_merge_mapping')
    flog.fields(merge_to=merge_to, merge_from=merge_from,
                inplace=inplace).debug('Entered _merge_mapping()')

    if inplace:
        dest = merge_to
    else:
        dest = merge_to.copy()

    for key, val in merge_from.items():
        if key in dest and isinstance(dest[key], MutableMapping) and \
                isinstance(val, MutableMapping):
            # Dict value so merge the value
            dest[key] = _merge_mapping(dest[key], val, inplace=inplace)
        else:
            dest[key] = val

    flog.fields(dest=dest).debug('Leaving _merge_mapping()')
    return dest


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
    flog = mlog.fields(func='_read_config')
    flog.fields(paths=paths, testing=testing).debug('Entering _read_config()')

    cfg = yaml.safe_load(DEFAULT_CONFIG)
    CONFIG_SCHEMA(cfg)

    for cfg_file in paths:
        try:
            with open(cfg_file, 'rb') as f:
                new_cfg = yaml.safe_load(f)
        except yaml.MarkedYAMLError as e:
            raise MagnateConfigError('Config error parsing {}:\n{}'.format(cfg_file, e))

        _merge_mapping(cfg, new_cfg, inplace=True)

        try:
            CONFIG_SCHEMA(cfg)
        except MultipleInvalid as e:
            raise MagnateConfigError('Config error in {}:\n{}'.format(cfg_file, e))

    if testing:
        testing_cfg = yaml.safe_load(TESTING_CONFIG)
        _merge_mapping(cfg, testing_cfg, inplace=True)
        CONFIG_SCHEMA(cfg)

    flog.fields(cfg=cfg).debug('Leaving _read_config()')
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
    flog = mlog.fields(func='_read_config')
    flog.fields(conf_file=conf_files, testing=testing).info('Entering read_config()')

    cfg_paths = _find_config(conf_files)
    cfg = _read_config(cfg_paths, testing)

    flog.fields(cfg=cfg).info('Leaving read_config()')
    return cfg


def write_default_config(filename):
    """
    Write out a default config file appropriate for a user to customize.

    :arg filename: The file path to write the config to.
    """
    flog = mlog.fields(func='write_default_config')
    flog.fields(filename=filename).info('Entering write_default_config()')

    with open(filename, 'w') as f:
        f.write(DEFAULT_CONFIG)

    flog.debug('Leaving write_default_config()')

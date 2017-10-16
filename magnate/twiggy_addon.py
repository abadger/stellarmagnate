# Stellar Magnate - A space-themed commodity trading game
# Copyright (C) 2017 Toshio Kuratomi <toshio@fedoraproject.org>
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
Helpers for the twiggy logging framework
"""

import importlib

import twiggy
import twiggy.levels
from voluptuous import Any, Equal, Optional, Schema, Invalid, MultipleInvalid


__all__ = ('dict_config',)

def ValidFunction():
    def validator(value):
        parts = value.split('.')

        # Test for a function in globals named value
        if len(parts) == 1:
            try:
                return callable(globals()[value])
            except KeyError:
                raise Invalid('Could not find a function named {}'.format(value))

        # Find a module that we can import
        module = None
        for idx in range(len(parts) - 1, 0, -1):
            try:
                module = importlib.import_module('.'.join(parts[:idx]))
            except Exception:
                pass
            else:
                remainder = parts[idx:]
                break
        else:  # For-else
            raise Invalid('Could not import a module with a function specified by {}'.format(value))

        # Handle both Staticmethod (ClassName.staticmethod) and module global function (functionname)
        try:
            function = getattr(module, '.'.join(remainder))
        except AttributeError:
            raise Invalid('Could not find a function named {} in module {}'.format(remainder, parts[:idx]))

        # Finally check that it is a callable
        if not callable(function):
            raise Invalid('Identifier specified by {} is not a function'.format(value))

        # Return the found function
        return function

    return validator


TWIGGY_CONFIG_SCHEMA = Schema({
    'version': Equal('1.0'),
    'outputs': {
        str: {
            'output': ValidFunction(),
            Optional('args', default=[]): list,
            Optional('kwargs', default={}): dict,
            Optional('format', default=twiggy.formats.LineFormat): ValidFunction(),
        },
    },
    'emitters': {
        str: {
            'level': Any('CRITICAL', 'DEBUG', 'DISABLED', 'ERROR', 'INFO', 'NOTICE', 'WARNING'),
            'filters': Any([Schema({
                'filter': ValidFunction(),
                Optional('args', default=[]): list,
                Optional('kwargs', default={}): dict,
                })], None),
            'output_name': str
        },
    },
    }, required=True)


def clear_emitters(names=None):
    """
    Remove multiple emitters

    :kwarg names: An optional list of emitter names to remove.  If this is None (the default) then
        all emitters are removed
    """
    if names:
        for emitter_name in names:
            del twiggy.emitters[emitter_name]
    else:
        twiggy.emitters.clear()


def dict_config(config):
    """
    Configure twiggy logging via a dictionary

    :arg config: a dictionary which configures twiggy's outputs and emitters.  See
        :attr:`TWIGGY_CONFIG_SCHEMA` for details of the format of the dict.
    :raises :exc:`voluptuous.MultipleInvalid`: if the config is incorrect.

    .. seealso:: :ref:`twiggy_setup.py` for a thorough explaination of the outputs and emitters
        concepts from the dictionary
    """
    # This will raise voluptuous.MultipleInvalid if there's an error.  For now, just propogate that
    try:
        cfg = TWIGGY_CONFIG_SCHEMA(config)
    except MultipleInvalid as e:
        twiggy.internal_log.info("Error in parsing the emitter setup: {0}".format(e))
        # XXX Looks like twiggy does not generate fatal errors on setup.  Instead it generates
        # errors on usage. (If this changes, could re-raise exception here)
        return

    outputs = {}
    for name, output in cfg['outputs'].items():
        outputs[name] = output['output'](*output['args'], **output['kwargs'], format=output['format'])

    emitters = []
    for name, emitter in cfg['emitters'].items():
        # Haven't figured out how to make voluptuous values depend on one another so check this here
        if emitter['output_name'] not in outputs:
            twiggy.internal_log.info("Encountered an undefined output_name: {0} for emitter {1}."
                                     " Omitting that emitter".format(emitter['output_name'], name))
            # XXX Looks like twiggy does not generate fatal errors on setup.  Instead it generates
            # errors on usage. (If this changes, could raise exception here)
            continue

        if not emitter['filters']:
            filters = None
        else:
            filters = []
            for filter_ in emitter['filters']:
                filters.append(filter_['filter'](*filter_['args'], **filter_['kwargs']))

        level = getattr(twiggy.levels, emitter['level'])
        emitters.append((name, level, filters, outputs[emitter['output_name']]))

    clear_emitters()
    twiggy.add_emitters(*emitters)

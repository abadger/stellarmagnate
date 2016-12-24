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
Helper functions for python attrs classes.
"""

def enum_converter(EnumType, value):
    """
    Convert a string into an :class:`enum.Enum`

    :arg EnumType: An Enum type to convert to
    :arg value: The value to convert to an Enum

    Typically, this function will be used with the :meth:`attr.ib` convert
    parameter and :func:`functools.partial`.  Example::

        @attr.s
        class CommodityData:
            type = attr.ib(convert=partial(enum_converter, CommodityType))
    """
    if not isinstance(value, EnumType):
        try:
            return EnumType[value]
        except:
            # Let the validator catch this
            pass
    return value


def enum_validator(EnumType, instance, attribute, value):
    """
    Validate that a value is a member of an :class:`enum.Enum`

    :arg EnumType: An Enum type to convert to
    :arg instance: The instance of the attr.s class that is being created
    :arg attribute: The attribute of the attr.s class that is being set
    :arg value: The value the attribute is being set to

    This function will be used with the :meth:`attr.ib` validate parameter and
    :func:`functools.partial`.  Example::

        @attr.s
        class CommodityData:
            type = attr.ib(validator=partial(enum_validator, CommodityType))
    """
    if not isinstance(value, EnumType):
        raise ValueError('{} is not a {}'.format(value, EnumType))

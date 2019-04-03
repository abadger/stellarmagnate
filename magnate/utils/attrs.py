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
Helper functions for python attrs classes.
"""

from collections.abc import MutableSequence, Sequence


def container_validator(container_type, instance, attribute, value,
                        not_container_type=None, contained_validator=None):
    """
    Validate that a value is a specific type of container and contains certain types of things

    :arg container_type: Type of container (example: collections.abc.Set)
    :arg instance: Instance of the class that we're validating
    :arg attribute: Name of the attribute that we're validating
    :arg value: Value of the attribute that we're validating
    :kwarg not_container_type: If not None (the default), a type that the
        container cannot be.  This can be used with collections.abc to specify
        immutability.  For instance, to specify only immutable sets::

            partial(container_validator, collections.abc.Set, not_container_type=collections.abc.MutableSet)

    :kwarg contained_validator: Another attr validator to run on each of the
        items inside of the container.
    """
    if not isinstance(value, container_type):
        try:
            type_name = container_type.__name__
        except AttributeError:
            type_name = container_type
        raise ValueError('{} is not of type {}'.format(value, type_name))

    if not_container_type is not None and isinstance(value, not_container_type):
        try:
            not_type_name = container_type.__name__
        except AttributeError:
            not_type_name = container_type
        raise ValueError('{} must not be of type {}'.format(value, not_type_name))

    if contained_validator is not None:
        for entry in value:
            try:
                contained_validator(instance, attribute, entry)
            except ValueError as e:
                raise ValueError('This element of the container: {}, did not validate: {}'.format(entry, e))


def container_converter(container_type, value, contained_converter=None):
    """
    Convert a container into another container type and convert the contained elements as well

    :arg container_type: The container type to convert into.
    :arg value: The value being converted
    :kwarg contained_converter: Converter to run over each element.

    Containers must be iterables.  The container may lose information.
    Containers to convert into cannot be a dict.  If converting from
    a Mapping, the value of the Mapping (not the key) is plaed into the new
    container.
    """
    if contained_converter is not None:
        value = container_type(contained_converter(i) for i in value)
    elif not isinstance(value, container_type):
        value = container_type(value)
    return value


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
        except Exception:
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


def sequence_of_type(_type, mutable, instance, attribute, value):
    """
    Validate that a value is a Sequence containing a specific type.

    :arg _type: The type of the values inside of the sequence
    :arg mutable: selects whether a sequence can be mutable or not
        :mutable: only mutable sequences are allowed
        :immutable: only immutable sequences are allowed
        :both: both mutable and immutable sequences are allowed
    :arg instance: The instance of the attr.s class that is being created
    :arg attribute: The attribute of the attr.s class that is being set
    :arg value: The value the attribute is being set to

    This function will be used with the :meth:`attr.ib` validate parameter and
    :func:`functools.partial`.  Example::

        @attr.s
        class CommodityData:
            type = attr.ib(validator=partial(enum_validator, CommodityType))
    """
    if mutable == 'both':
        msg = 'a Sequence'
    elif mutable == 'mutable':
        msg = 'a MutableSequence'
    elif mutable == 'immutable':
        msg = 'an Immutable Sequence'
    else:
        raise ValueError('sequence_of_type was given an improper argument for mutable')

    if not isinstance(value, Sequence):
        raise ValueError('{} is not {}'.format(value, msg))

    if isinstance(value, MutableSequence):
        if mutable == 'immutable':
            raise ValueError('{} is not {}'.format(value, msg))
    else:
        if mutable == 'mutable':
            raise ValueError('{} is not {}'.format(value, msg))

    for entry in value:
        if not isinstance(entry, _type):
            raise ValueError('The Sequence element {} is not a {}'.format(value, _type))

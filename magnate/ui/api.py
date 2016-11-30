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
Defines the API for Stellar Magnate client UserInterface plugins.

See also the documentation on events for the communication between the
frontend and backend.
"""

from abc import ABCMeta, abstractmethod


class UserInterface(metaclass=ABCMeta):
    """The main entry point into a magnate User Interface

    Stellar Magnate clients must implement a subclass or UserInterface as
    their main entrypoint.
    """

    @abstractmethod
    def __init__(self, pubpen):
        """Initialize the UserInterface

        :arg pubpen: A :class:`pubmarine.PubPen` object for communicating
            between the UserInterface and the :class:`magnate.Dispatcher`.
            This can safely be used to communicate between pieces of the user
            interface as well as long as you don't publish on an existing channel.
            The pubpen contains a link to the asyncio event loop that may be
            shared by the UserInterface if it supports it.
        """
        self.pubpen = pubpen

    @abstractmethod
    def run(self):
        """Run the interface

        This runs the magnate program.  Since the entire program is event
        driven, it must start the asyncio event loop and the user interface
        event loop (if different).
        """
        pass

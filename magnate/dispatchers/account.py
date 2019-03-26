# Stellar Magnate - A space-themed commodity trading game
# Copyright (C) 2019 Toshio Kuratomi <toshio@fedoraproject.org>
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
.. py:function:: action.account.login_attempt(username: string, password: string)

    Emitted when the user submits credentials to login.  This can trigger
    a :py:func:`user.login_success` or :py:func:`user.login_failure` event.

    :arg string username: The name of the user attempting to login
    :arg string password: The password for the user

.. py:function:: action.account.new_user(username: string, password: string)
    Emitted when the user wants to create a new account

.. py:function:: action.account.new_game(savefile, username, shipname)

    Emitted when the user requests that a new game be created

.. py:function:: action.account.load_game(savefile)

    Emitted when the user requests that a file be used to load a new game.  If the file doesn't
    exist, a new game will be created under that filename.

"""

from __main__ import magnate

from .errors import MagnateAuthError


def login(username, password):
    try:
        magnate.login(username, password)
        magnate.pubpen.publish('user.login_succes', username)
    except MagnateAuthError as e:
        magnate.pubpen.publish('user.login_failure', username, reason=str(e))


def create_user(username, password):
    try:
        magnate.create_user(username, password)
        magnate.pubpen.publish('user.login_succes', username)
    except MagnateAuthError as e:
        magnate.pubpen.publish('user.login_failure', username, reason=str(e))


def list_games(username):
    pass

def create_new_game(savefile, username, shipname):
    pass


def load_game(savefile):
    pass


def register_event_handlers(pubpen):
    """Register event handlers"""
    pubpen.subscribe('action.account.login_attempt', login)
    pubpen.subscribe('action.account.new_user', create_user)
    pubpen.subscribe('action.account.new_game', create_new_game)
    pubpen.subscribe('action.account.load_game', load_game)

# Stellar Magnate - A space-themed commodity trading game
# Copyright (C) 2018 Toshio Kuratomi <toshio@fedoraproject.org>
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

import os

from twiggy import log

from ..errors import MagnateNoSaveGame
from . import db

#
# Upgrading
#

#
# Game setup mechanics
#

def init_game(savegame, datadir):
    """Initialize a game from a savegame"""
    # Finish initializing dynamic parts of the schema
    db.init_schema(datadir)

    savegame = os.path.abspath(savegame)
    try:
        game_state = db.load_savegame(savegame, datadir)
    except MagnateNoSaveGame:
        game_state = db.create_savegame(savegame, datadir)

    return game_state

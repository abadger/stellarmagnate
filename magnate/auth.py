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
import dbm
import os
import os.path
import stat

from passlib.context import CryptContext
import pwquality

from .errors import MagnateAuthError


class AccountDB:
    """Database to authenticate accounts"""
    def __init__(self, account_file, passlib_cfg):
        self.passlib_ctx = CryptContext(**passlib_cfg)
        self.pwquality_ctx = pwquality.PWQSettings()

        self.account_file = account_file

        # Make sure that the file exists
        if not os.path.exists(self.account_file):
            dbm.open(self.account_file, 'c', mode=0o600).close()
            os.chmod(self.account_file, 0o600)

        # Verify that the file's permissions are secure
        file_stats = os.stat(self.account_file, follow_symlinks=False)
        mode = stat.S_IMODE(file_stats.st_mode)

        if os.geteuid() != file_stats.st_uid:
            raise ValueError(f'Authentication db, {account_file}, must be owned by the same user'
                             ' as magnate process')
        if os.getegid() != file_stats.st_gid:
            raise ValueError(f'Authentication db, {account_file}, must be owned by the same group'
                             ' as magnate process')
        if mode != (stat.S_IRUSR | stat.S_IWUSR):
            raise ValueError(f'Authentication db, {account_file}, must have 0600 permissions and'
                             ' nothing else')

    def create_account(self, username, password):
        """Create a new user account"""
        try:
            self.pwquality_ctx.check(password)
        except pwquality.PWQError as e:
            raise MagnateAuthError('Password fails quality check: {}'.format(str(e)))

        with dbm.open(self.account_file, 'w') as account_db:
            if account_db.get(username) is not None:
                raise MagnateAuthError(f'account for {username} already exists')
            account_db[username] = self.passlib_ctx.hash(password)

    def authenticate(self, username, password):
        """Authenticate a user via a password"""
        with dbm.open(self.account_file, 'r') as account_db:
            try:
                password_hash = account_db[username]
            except KeyError:
                raise MagnateAuthError(f'Unknown user: {username}')

        authenticated, new_hash = self.passlib_ctx.verify_and_update(password, password_hash)
        if not authenticated:
            return False

        # If the current hashing strategy for the password isn't good enough
        if new_hash:
            with dbm.open(self.account_file, 'w') as account_db:
                account_db[username] = new_hash

        return True

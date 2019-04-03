# The idiom for unittests is to use classes for organization
# pylint: disable=no-self-use

import dbm
import os
import os.path
import stat

import pytest
from passlib.hash import pbkdf2_sha512

from magnate import auth
from magnate import errors


USERNAME = 'falkenberg'
GOOD_PASSWORD = 'Me81lo-a;x>s12dnzP;4'


@pytest.fixture
def accountdb(tmp_path):
    auth_file = tmp_path / 'authdb'
    yield auth.AccountDB(str(auth_file), {'schemes': ['pbkdf2_sha256', 'pbkdf2_sha512']})


@pytest.fixture
def populated_accountdb(accountdb):
    accountdb.create_account(USERNAME, GOOD_PASSWORD)
    yield accountdb


@pytest.fixture
def account_file(tmp_path):
    auth_file = tmp_path / 'authdb'
    with dbm.open(str(auth_file), 'c', 0o600) as auth_db:
        auth_db[USERNAME] = pbkdf2_sha512.hash(GOOD_PASSWORD)

    yield auth_file


class TestCreateAccountDB:
    def test_create_file(self, tmp_path):
        auth_file = tmp_path / 'authdb'
        assert not os.path.exists(auth_file)
        auth.AccountDB(str(auth_file), {'schemes': ['pbkdf2_sha512']})

        assert os.path.exists(auth_file)

        file_stats = os.stat(auth_file)
        assert file_stats.st_uid == os.geteuid()
        assert file_stats.st_gid == os.getegid()
        assert stat.S_IMODE(file_stats.st_mode) == 0o600

    def test_open_preexisting_file(self, account_file):
        accountdb = auth.AccountDB(str(account_file), {'schemes': ['pbkdf2_sha512']})

        assert os.path.exists(account_file)

        file_stats = os.stat(account_file)
        assert file_stats.st_uid == os.geteuid()
        assert file_stats.st_gid == os.getegid()
        assert stat.S_IMODE(file_stats.st_mode) == 0o600

        assert accountdb.authenticate(USERNAME, GOOD_PASSWORD)


    def test_preexisting_bad_user(self, account_file, monkeypatch):
        # Make sure that the function thinks our present uid is different from the one the file was
        # created with
        real_geteuid = os.geteuid
        monkeypatch.setattr(os, 'geteuid', lambda: real_geteuid() - 1)
        with pytest.raises(ValueError, match=r'must be owned by the same user as'
                           ' magnate process'):
            auth.AccountDB(str(account_file), {'schemes': ['pbkdf2_sha512']})

    def test_preexisting_bad_group(self, account_file, monkeypatch):
        real_getegid = os.getegid
        monkeypatch.setattr(os, 'getegid', lambda: real_getegid() - 1)
        with pytest.raises(ValueError, match=r'must be owned by the same group as'
                           ' magnate process'):
            auth.AccountDB(str(account_file), {'schemes': ['pbkdf2_sha512']})

    def test_preexisting_bad_mode(self, account_file, mocker, monkeypatch):
        real_stat = os.stat

        def fake_stat(*args, **kwargs):
            file_stats = real_stat(*args, **kwargs)
            file_type = stat.S_IFMT(file_stats.st_mode)
            file_mode = stat.S_IRUSR | stat.S_IWUSR | stat.S_IWGRP

            new_stats = list(file_stats)
            new_stats[stat.ST_MODE] = file_type | file_mode
            return os.stat_result(new_stats)

        monkeypatch.setattr(os, 'stat', fake_stat)

        with pytest.raises(ValueError, match=r'must have 0600 permissions and'
                           ' nothing else'):
            auth.AccountDB(str(account_file), {'schemes': ['pbkdf2_sha512']})


class TestCreateAccount:
    def test_successful_account_creation(self, accountdb):
        with dbm.open(accountdb.account_file, 'r') as database:
            assert USERNAME not in database

        accountdb.create_account(USERNAME, GOOD_PASSWORD)

        with dbm.open(accountdb.account_file, 'r') as database:
            assert USERNAME in database

        # smoketest
        accountdb.authenticate(USERNAME, GOOD_PASSWORD)

    @pytest.mark.parametrize('password', ['aaaa', 'encyclopedia', '123', 'shw6c-1'])
    def test_poor_password(self, accountdb, password):
        with pytest.raises(errors.MagnateAuthError) as err:
            accountdb.create_account(USERNAME, password)

        assert err.value.args[0].startswith('Password fails quality check: ')

    def test_error_account_exists(self, accountdb):
        accountdb.create_account(USERNAME, GOOD_PASSWORD)

        with dbm.open(accountdb.account_file, 'r') as database:
            assert USERNAME in database

        with pytest.raises(errors.MagnateAuthError) as err:
            accountdb.create_account(USERNAME, GOOD_PASSWORD)

        assert err.value.args[0] == f'account for {USERNAME} already exists'


class TestAuthenticate:
    def test_bad_username(self, populated_accountdb):
        with pytest.raises(errors.MagnateAuthError) as err:
            populated_accountdb.authenticate('nonexistent', GOOD_PASSWORD)

        assert err.value.args[0] == 'Unknown user: nonexistent'

    def test_bad_password(self, populated_accountdb):
        assert populated_accountdb.authenticate(USERNAME, '12asdw3vq-45') is False

    def test_good_login(self, populated_accountdb):
        with dbm.open(populated_accountdb.account_file, 'r') as database:
            password_hash = database[USERNAME]

        assert populated_accountdb.authenticate(USERNAME, GOOD_PASSWORD) is True

        # Assert that the hash did not change
        with dbm.open(populated_accountdb.account_file, 'r') as database:
            assert password_hash == database[USERNAME]

    def test_good_login_with_rehash(self, populated_accountdb):
        with dbm.open(populated_accountdb.account_file, 'r') as database:
            password_hash = database[USERNAME]

        populated_accountdb.passlib_ctx.update({'deprecated': ['pbkdf2_sha256']})
        assert populated_accountdb.authenticate(USERNAME, GOOD_PASSWORD) is True

        # Assert that the hash was updated
        with dbm.open(populated_accountdb.account_file, 'r') as database:
            assert password_hash != database[USERNAME]

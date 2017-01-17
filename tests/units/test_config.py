import os.path

import pytest

from magnate import config as c


class TestFindConfig:
    @staticmethod
    def _sm_paths_exist(path):
        if path.endswith('sm.cfg'):
            return True
        else:
            return False

    def test_defaults_none_exist(self, mocker):
        mocker.patch('os.path.exists', autospec=True, side_effect=lambda path: False)
        results = c._find_config()
        assert results == []

    def test_defaults_all_exist(self, mocker):
        mocker.patch('os.path.exists', autospec=True, side_effect=lambda path: True)
        results = c._find_config()
        assert results == ['/etc/stellarmagnate/magnate.cfg', os.path.expanduser('~/.stellarmagnate/magnate.cfg')]

    def test_extra_conf_files_all_exist(self, mocker):
        mocker.patch('os.path.exists', autospec=True, side_effect=lambda path: True)
        results = c._find_config(conf_files=('/srv/sm/magnate.cfg', '~/sm.cfg'))
        assert results == ['/etc/stellarmagnate/magnate.cfg',
                           os.path.expanduser('~/.stellarmagnate/magnate.cfg'),
                           '/srv/sm/magnate.cfg',
                           os.path.expanduser('~/sm.cfg'),
                          ]

    def test_extra_conf_files_none_exist(self, mocker):
        mocker.patch('os.path.exists', autospec=True, side_effect=lambda path: False)
        results = c._find_config(conf_files=('/srv/sm/magnate.cfg', '~/sm.cfg'))
        assert results == []

    def test_extra_conf_files_some_exist(self, mocker):
        mocker.patch('os.path.exists', autospec=True, side_effect=self._sm_paths_exist)
        results = c._find_config(conf_files=('/srv/sm/magnate.cfg', '~/sm.cfg'))
        assert results == [ os.path.expanduser('~/sm.cfg') ]


class Test_ReadConfig:
    def test_something(self):
        pass


class TestReadConfig:
    def test_something(self):
        pass


class TestWriteDefaultConfig:
    def test_something(self):
        pass

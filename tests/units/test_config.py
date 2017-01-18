import os.path

import pytest

from magnate import config as c
from magnate import errors

class Test_FindConfig:
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
    cfg_keys = frozenset(('base_data_dir', 'schema_dir', 'save_dir', 'ui_plugin'))

    ui_and_schema = """
    # This is a sample config file
    # that sets ui_plugin and schema directory
    ui_plugin = the_bestest_widget_set
    schema_dir = /dev/zero
    """

    ui_and_schema_cfg = """
    # This is a sample config file
    # that sets ui_plugin and schema directory
    ui_plugin = the_bestest_widget_set
    schema_dir = /dev/zero
    """

    all_cfg = """
    # This is a sample config file
    # that sets ui_plugin and schema directory
    ui_plugin = the_bestest_widget_set
    schema_dir = /dev/zero
    save_dir = /tmp
    base_data_dir = /tmp
    """

    extra_cfg = """
    # This is a sample config file
    # that sets ui_plugin and schema directory
    ui_plugin = the_bestest_widget_set
    schema_dir = /dev/zero
    schwartzchilde = limit
    """

    bad_cfg = """
    ui_plugin = Make an ultra long string that does not satisfy the needs of the validator for the ui plugin.  Eventually could write a validator that handles other things besides length but.... not yet.
    """

    not_ini_cfg = """
    ][
    strussel
    5
    ***
    """

    def test_pure_default(self):
        cfg = c._read_config(tuple())

        assert self.cfg_keys.symmetric_difference(cfg.keys()) == frozenset()
        assert cfg['base_data_dir'] == '/usr/share/stellarmagnate/base'
        assert cfg['schema_dir'] == '/usr/share/stellarmagnate/schemas'
        assert cfg['save_dir'] == '~/.stellarmagnate/saves'
        assert cfg['ui_plugin'] == 'urwid'

    def test_paths_given_some_default_override(self, mocker):
        m = mocker.mock_open(read_data=self.ui_and_schema_cfg)
        mocker.patch('builtins.open', m)
        mocker.patch('os.path.isfile', autospec=True, side_effect=lambda path: True)
        cfg = c._read_config(('/fake/path/sm-ui-and-schema.cfg',))
        cfg_keys = frozenset(('base_data_dir', 'schema_dir', 'save_dir', 'ui_plugin'))

        assert self.cfg_keys.symmetric_difference(cfg.keys()) == frozenset()
        assert cfg['base_data_dir'] == '/usr/share/stellarmagnate/base'
        assert cfg['schema_dir'] == '/dev/zero'
        assert cfg['save_dir'] == '~/.stellarmagnate/saves'
        assert cfg['ui_plugin'] == 'the_bestest_widget_set'

    def test_paths_given_all_default_override(self, mocker):
        m = mocker.mock_open(read_data=self.all_cfg)
        mocker.patch('builtins.open', m)
        mocker.patch('os.path.isfile', autospec=True, side_effect=lambda path: True)
        cfg = c._read_config(('/fake/path/sm-all.cfg',))

        assert self.cfg_keys.symmetric_difference(cfg.keys()) == frozenset()
        assert cfg['base_data_dir'] == '/tmp'
        assert cfg['schema_dir'] == '/dev/zero'
        assert cfg['save_dir'] == '/tmp'
        assert cfg['ui_plugin'] == 'the_bestest_widget_set'

    def test_invalid_config(self, mocker):
        m = mocker.mock_open(read_data=self.not_ini_cfg)
        mocker.patch('builtins.open', m)
        mocker.patch('os.path.isfile', autospec=True, side_effect=lambda path: True)

        with pytest.raises(errors.MagnateConfigError) as e:
            cfg = c._read_config(('/fake/path/sm-not-ini.cfg',))
        assert '/fake/path/sm-not-ini.cfg' in e.value.args[0]

    def test_extra_config(self, mocker):
        m = mocker.mock_open(read_data=self.extra_cfg)
        mocker.patch('builtins.open', m)
        mocker.patch('os.path.isfile', autospec=True, side_effect=lambda path: True)

        with pytest.raises(errors.MagnateConfigError) as e:
            cfg = c._read_config(('/fake/path/sm-extra.cfg',))
        assert '/fake/path/sm-extra.cfg' in e.value.args[0]
        assert 'schwartzchilde' in e.value.args[0]

    def test_bad_config(self, mocker):
        m = mocker.mock_open(read_data=self.bad_cfg)
        mocker.patch('builtins.open', m)
        mocker.patch('os.path.isfile', autospec=True, side_effect=lambda path: True)

        with pytest.raises(errors.MagnateConfigError) as e:
            cfg = c._read_config(('/fake/path/sm-bad.cfg',))
        assert '/fake/path/sm-bad.cfg' in e.value.args[0]
        assert 'ui_plugin' in e.value.args[0]
        assert 'VdtValueTooLongError' in e.value.args[0]

    def test_pure_testing(self):
        cfg = c._read_config(tuple(), testing=True)
        cfg_keys = frozenset(('base_data_dir', 'schema_dir', 'save_dir', 'ui_plugin'))

        assert self.cfg_keys.symmetric_difference(cfg.keys()) == frozenset()
        assert cfg['base_data_dir'] == os.path.normpath(os.path.join(os.path.dirname(__file__), '../../', 'data'))
        assert cfg['schema_dir'] == os.path.normpath(os.path.join(os.path.dirname(__file__), '../../', 'data'))
        assert cfg['save_dir'] == '~/.stellarmagnate/saves'
        assert cfg['ui_plugin'] == 'urwid'

    def test_paths_and_testing(self, mocker):
        m = mocker.mock_open(read_data=self.ui_and_schema_cfg)
        mocker.patch('builtins.open', m)
        mocker.patch('os.path.isfile', autospec=True, side_effect=lambda path: True)
        cfg = c._read_config(('/fake/path/sm-ui-and-schema.cfg',), testing=True)

        assert self.cfg_keys.symmetric_difference(cfg.keys()) == frozenset()
        assert cfg['base_data_dir'] == os.path.normpath(os.path.join(os.path.dirname(__file__), '../../', 'data'))
        assert cfg['schema_dir'] == os.path.normpath(os.path.join(os.path.dirname(__file__), '../../', 'data'))
        assert cfg['save_dir'] == '~/.stellarmagnate/saves'
        assert cfg['ui_plugin'] == 'the_bestest_widget_set'
        pass


class TestReadConfig:
    def test_something(self, mocker):
        find_config = mocker.MagicMock(return_value=('foo', 'bar'))
        read_config = mocker.MagicMock()
        mocker.patch('magnate.config._find_config', find_config)
        mocker.patch('magnate.config._read_config', read_config)
        cfg = c.read_config()

        assert find_config.called is True
        assert find_config.call_count == 1
        assert find_config.call_args[0] == tuple([tuple()])
        assert read_config.called is True
        assert read_config.call_count == 1
        assert read_config.call_args[0] == (('foo', 'bar'), False)


class TestWriteDefaultConfig:
    def test_writing_file(self, tmpdir):
        conf_file = tmpdir.join('sm.cfg')
        c.write_default_config(str(conf_file))

        assert c.DEFAULT_CONFIG == open(str(conf_file)).read().split('\n')

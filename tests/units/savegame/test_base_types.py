import builtins
import os.path
import re
from unittest.mock import mock_open, patch

import pytest
from voluptuous.error import Error as VError

from magnate.savegame import base_types


INVALID_DATA = (
        ('''{version: "1.0", types: {CommodityType: []}}''', VError,
            ("not a valid value for dictionary value @ data\\['version']. Got '1.0'",)),
        ('''{version: "0.1", tpyes: {}}''', VError,
            ("extra keys not allowed @ data\\['tpyes']",
             "required key not provided @ data\\['types']")),
        ('''{version: "0.1", types: []}''', VError,
            ("expected a dictionary for dictionary value @ data\\['types']",)),
        ('''{version: "0.1", types: {10: []}}''', VError,
            ("extra keys not allowed @ data\\['types']\\[10]",)),
        ('''{version: "0.1", types: {Commodity: []}}''', VError,
            ("extra keys not allowed @ data\\['types']\\['Commodity']",)),
        ('''{version: "0.1", types: {commodityType: []}}''', VError,
            ("extra keys not allowed @ data\\['types']\\['commodityType']",)),
        )


class TestLoadBaseTypes:
    def test_valid_types(self):
        """
        Test that valid types are loaded from a data file.

        This also tests that the function works with real data.
        """
        datadir = os.path.join(os.path.dirname(__file__), 'data')
        data = base_types.load_base_types(datadir)
        assert data == {'types': {'CommodityType': ['food', 'material'],
                                  'CelestialType': ['asteroid'],
                                  'GovernmentType': ['democracy', 'dictatorship']},
                        'version': '0.1'}

    def test_invalid_directory(self):
        """Test that invalid filename raise an exception"""
        with pytest.raises(FileNotFoundError):
            data = base_types.load_base_types("123")

    @pytest.mark.parametrize('data, exc, msg_match', INVALID_DATA)
    def test_invalid_types(self, data, exc, msg_match):
        """Test that invalid types raise an exception"""

        with patch('builtins.open', mock_open(read_data=data)):
            with pytest.raises(exc) as excinfo:
                data = base_types.load_base_types("123")

        for msg in msg_match:
            assert re.search(msg, excinfo.value.args[0])


def test_init_base_types():
    """Test that base Types are initialized when this is run"""

    data = """---
    version: "0.1"
    types:
      TestType:
        - a test
    """

    assert not hasattr(base_types, "TestType")

    with patch('builtins.open', mock_open(read_data=data)):
        base_types.init_base_types("123")

    assert hasattr(base_types, "TestType")

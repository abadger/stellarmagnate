import builtins
import enum
import os.path
import re
from unittest.mock import mock_open, patch

import pytest
from voluptuous.error import Error as VError

from magnate.savegame import base_types


pytestmark = pytest.mark.usefixtures('clean_context')


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


@pytest.fixture
def test_type(clean_context):
    data = """---
    version: "0.1"
    types:
      TestType:
        - test_one
        - test_two
    """

    with patch('builtins.open', mock_open(read_data=data)):
        base_types.init_base_types("123")

    return base_types.TestType


@pytest.fixture
def broken_test_type(test_type):
    def _fake_getitem(self, value):
        raise OSError('getitem raised an unexpected exception')

    old_getitem = test_type.__class__.__getitem__
    test_type.__class__.__getitem__ = _fake_getitem
    yield test_type

    test_type.__class__.__getitem__ = old_getitem


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
        - test_one
        - test_two
    """

    assert not hasattr(base_types, "TestType")

    with patch('builtins.open', mock_open(read_data=data)):
        base_types.init_base_types("123")

    assert hasattr(base_types, "TestType")
    assert hasattr(base_types.TestType, "validator")
    assert isinstance(base_types.TestType, enum.EnumMeta)


@pytest.mark.parametrize('enum_value', ('test_one', 'test_two'))
def test_base_types_enum_validator_good(test_type, enum_value):
    assert isinstance(test_type.validator(enum_value), enum.Enum)
    assert isinstance(test_type.validator(enum_value), test_type)
    assert test_type.validator(enum_value) is test_type[enum_value]


def test_base_types_enum_validator_bad_key(test_type):
    with pytest.raises(ValueError) as excinfo:
        test_type.validator('test_bad')
    assert excinfo.value.args[0] == 'test_bad is not a valid member of TestType'


def test_base_types_enum_validator_exception_with_nonmember(broken_test_type):
    with pytest.raises(ValueError) as excinfo:
        broken_test_type.validator('test_bad')

    assert excinfo.value.args[0] == 'test_bad is not a TestType'


def test_base_types_enum_validator_exception_with_member(broken_test_type):
    with pytest.raises(OSError) as excinfo:
        broken_test_type.validator(broken_test_type.test_one)

    assert excinfo.value.args[0] == 'getitem raised an unexpected exception'

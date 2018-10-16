import copy
import os

import pytest
import voluptuous
import voluptuous.error
from voluptuous.humanize import validate_with_humanized_errors as v_validate

from magnate.savegame import base_types
from magnate.savegame import data_def


pytestmark = pytest.mark.usefixtures('clean_context')


@pytest.fixture
def setup_base_types(datadir, clean_context):
    base_types.init_base_types(datadir)
    yield


# Tests for voluptuous validators
class TestValidators:
    def test_known_celestial(self):
        data = {'systems': [
                   {'celestials': [
                        {'name': 'Mercury'},
                        {'name': 'Venus'},
                    ],
                    'locations': [
                        {'celestial': 'Mercury'},
                        {'celestial': 'Mercury'},
                        {'celestial': 'Venus'},
                    ],
                },
               ]}
        assert data_def.known_celestial(data) == data

    def test_known_celestial_failure(self):
        data = {'systems': [
                   {'celestials': [
                        {'name': 'Mercury'},
                        {'name': 'Venus'},
                    ],
                    'locations': [
                        {'celestial': 'Mercury'},
                        {'celestial': 'Venus'},
                        {'celestial': 'Earth'},
                    ],
                },
               ]}

        with pytest.raises(voluptuous.error.Invalid) as excinfo:
            validated_output = data_def.known_celestial(data)

        assert excinfo.value.args[0] == 'locations must belong to a known celestial, not Earth'

    @pytest.mark.parametrize("locations", [{'celestial': 'Venus'},
                                           # Fine to have two locations on the same celestial
                                           {'celestial': 'Mercury'},
                                          ])
    def test_known_celestial(self, locations):
        data = {'systems': [
                   {'celestials': [
                        {'name': 'Mercury'},
                        {'name': 'Venus'},
                    ],
                    'locations': [
                        {'celestial': 'Mercury'},
                    ],
                },
               ]}
        data['systems'][0]['locations'].append(locations)
        assert data_def.known_celestial(data) == data

    def test_known_celestial_failure(self):
        data = {'systems': [
                   {'celestials': [
                        {'name': 'Mercury'},
                        {'name': 'Venus'},
                    ],
                    'locations': [
                        {'celestial': 'Mercury'},
                        {'celestial': 'Venus'},
                        {'celestial': 'Earth'},
                    ],
                },
               ]}

        with pytest.raises(voluptuous.error.Invalid) as excinfo:
            validated_output = data_def.known_celestial(data)
        assert excinfo.value.args[0] == 'locations must belong to a known celestial, not Earth'

    @pytest.mark.parametrize('parts', [{'volume': 10, 'storage': None},
                                       {'volume': None, 'storage': 10},
                            ])
    def test_volume_or_storage(self, parts):
        data = {'ship_parts': [ parts ]}

        assert data_def.volume_or_storage(data) == data

    @pytest.mark.parametrize('parts', [{'name': 'foo', 'volume': 10, 'storage': 1},
                                       {'name': 'foo', 'volume': None, 'storage': None},
                            ])
    def test_volume_or_storage_failure(self, parts):
        data = {'ship_parts': [ parts ]}

        with pytest.raises(voluptuous.error.Invalid) as excinfo:
            validated_output = data_def.volume_or_storage(data)

        assert excinfo.value.args[0] == 'ship_part foo must either take up room or add room'


@pytest.mark.usefixtures('setup_base_types')
def test_define_schemas(datadir):
    data_def._define_schemas(datadir)

    assert isinstance(data_def.BASE_SCHEMA, voluptuous.Schema)
    assert isinstance(data_def.SYSTEM_SCHEMA, voluptuous.Schema)


GOOD_BASE_DATA = {'version': '0.1',
                  'ships': [
                      {'name': 'Ship',
                       'mean_price': 1,
                       'standard_deviation': 2,
                       'depreciation_rate': 3,
                       'storage': 4,
                       'weapon_mounts': 5,
                      },
                      ],
                  'property': [
                      {'name': 'Warehouse',
                       'mean_price': 1,
                       'standard_deviation': 2,
                       'depreciation_rate': 3,
                       'storage': 4,
                      },
                      ],
                  'ship_parts': [
                      {'name': 'Hold',
                       'mean_price': 1,
                       'standard_deviation': 2,
                       'depreciation_rate': 3,
                       'storage': 4,
                      },
                      ],
                  'events': [
                      {'msg': 'Something happened!',
                       'adjustment': 10,
                       'affects': [
                           'food',
                           ]
                       }
                      ],
                  }


GOOD_SYSTEM_DATA = {'version': '0.1',
                    'systems': [
                        {'name': 'Test System',
                         'celestials': [
                             {'name': 'Friesland',
                              'orbit': 1,
                              'type': 'rocky'
                             },
                             ],
                         'locations': [
                             {'name': 'Graffenburg',
                              'type': 'dome',
                              'celestial': 'Friesland'
                             },
                             ],
                         'commodities': [
                             {'name': 'Computers',
                              'categories': ['machinery'],
                              'mean_price': 1,
                              'standard_deviation': 2,
                              'depreciation_rate': 3,
                              'volume': 4,
                              },
                             ],
                         },
                         ],
                    }


def good_base_data():
    data = copy.deepcopy(GOOD_BASE_DATA)
    yield data

    data = copy.deepcopy(GOOD_BASE_DATA)
    data['events'][0]['affects'][0] = ['food', 'illegal']
    yield data

    data = copy.deepcopy(GOOD_BASE_DATA)
    data['events'][0]['affects'] = ['food', 'illegal']
    yield data

    data = copy.deepcopy(GOOD_BASE_DATA)
    data['events'][0]['affects'] = ['food', ['chemical', 'illegal']]
    yield data

    data = copy.deepcopy(GOOD_BASE_DATA)
    data['ship_parts'][0]['storage'] = None
    data['ship_parts'][0]['volume'] = 10
    yield data


def good_system_data():
    data = copy.deepcopy(GOOD_SYSTEM_DATA)
    yield data

    data = copy.deepcopy(GOOD_SYSTEM_DATA)
    data['systems'][0]['commodities'][0]['categories'] = ['food', 'illegal']
    yield data


def bad_base_data():
    data = copy.deepcopy(GOOD_BASE_DATA)
    data['version'] = '100.0'
    yield (data, "not a valid value for dictionary value @ data['version']")

    data = copy.deepcopy(GOOD_BASE_DATA)
    data['version'] = 0.1
    yield (data, "not a valid value for dictionary value @ data['version']")

    data = copy.deepcopy(GOOD_BASE_DATA)
    del data['ships'][0]['name']
    yield (data, "required key not provided @ data['ships'][0]['name']")

    data = copy.deepcopy(GOOD_BASE_DATA)
    data['ship_parts'][0]['volume'] = None
    data['ship_parts'][0]['storage'] = None
    yield (data, "ship_part Hold must either take up room or add room")

    data = copy.deepcopy(GOOD_BASE_DATA)
    data['ship_parts'][0]['volume'] = 1
    data['ship_parts'][0]['storage'] = 1
    yield (data, "ship_part Hold must either take up room or add room")

    data = copy.deepcopy(GOOD_BASE_DATA)
    data['events'][0]['affects'] = ['nothing']
    yield (data, "not a valid value @ data['events'][0]['affects'][0]")

    data = copy.deepcopy(GOOD_BASE_DATA)
    data['events'][0]['affects'] = ['food', ['nothing', 'food']]
    yield (data, "not a valid value @ data['events'][0]['affects'][1][0]")


def bad_system_data():
    data = copy.deepcopy(GOOD_SYSTEM_DATA)
    data['version'] = '100.0'
    yield (data, "not a valid value for dictionary value @ data['version']")

    data = copy.deepcopy(GOOD_SYSTEM_DATA)
    data['version'] = 0.1
    yield (data, "not a valid value for dictionary value @ data['version']")

    data = copy.deepcopy(GOOD_SYSTEM_DATA)
    data['systems'][0]['celestials'][0]['type'] = 'blender'
    yield (data, "not a valid value for dictionary value @ data['systems'][0]['celestials'][0]['type']")

    data = copy.deepcopy(GOOD_SYSTEM_DATA)
    data['systems'][0]['locations'][0]['type'] = 'blender'
    yield (data, "not a valid value for dictionary value @ data['systems'][0]['locations'][0]['type']")

    data = copy.deepcopy(GOOD_SYSTEM_DATA)
    data['systems'][0]['locations'][0]['celestial'] = 'blender'
    yield (data, "locations must belong to a known celestial, not blender")

    data = copy.deepcopy(GOOD_SYSTEM_DATA)
    data['systems'][0]['commodities'][0]['categories'] = 'food'
    yield (data, "expected a list for dictionary value @ data['systems'][0]['commodities'][0]['categories']")

    data = copy.deepcopy(GOOD_SYSTEM_DATA)
    data['systems'][0]['commodities'][0]['categories'] = ['nothing']
    yield (data, "not a valid value @ data['systems'][0]['commodities'][0]['categories'][0]")

    data = copy.deepcopy(GOOD_SYSTEM_DATA)
    data['systems'][0]['commodities'][0]['categories'] = ['food', 'nothing']
    yield (data, "not a valid value @ data['systems'][0]['commodities'][0]['categories'][1]")


@pytest.mark.usefixtures('setup_base_types')
class TestSchemas:
    @pytest.mark.parametrize('good_data', good_base_data())
    def test_base_schema(self, datadir, good_data):
        print(base_types.CommodityType)
        print(base_types.CommodityType.__members__)
        print(base_types.CommodityType.validator('food'))
        data_def._define_schemas(datadir)
        assert v_validate(good_data, data_def.BASE_SCHEMA)

    @pytest.mark.parametrize('good_data', good_system_data())
    def test_system_schema(self, datadir, good_data):
        data_def._define_schemas(datadir)
        assert v_validate(good_data, data_def.SYSTEM_SCHEMA)

    @pytest.mark.parametrize('bad_data, error_msg', bad_base_data())
    def test_base_schema_fail(self, datadir, bad_data, error_msg):
        data_def._define_schemas(datadir)

        with pytest.raises(voluptuous.error.Invalid) as excinfo:
            assert data_def.BASE_SCHEMA(bad_data)

        assert str(excinfo.value) == error_msg

    @pytest.mark.parametrize('bad_data, error_msg', bad_system_data())
    def test_system_schema_fail(self, datadir, bad_data, error_msg):
        data_def._define_schemas(datadir)
        with pytest.raises(voluptuous.error.Invalid) as excinfo:
            assert data_def.SYSTEM_SCHEMA(bad_data)

        assert str(excinfo.value) == error_msg

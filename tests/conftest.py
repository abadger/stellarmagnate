import os.path

import pytest

from magnate.savegame import base_types, db, data_def


@pytest.fixture
def clean_context():
    old_engine = db.engine
    db.engine = None

    old_types = {}
    for key, value in base_types.__dict__.items():
        if key.endswith('Type'):
            old_types[key] = value

    old_system_schema = data_def.SYSTEM_SCHEMA
    old_base_schema = data_def.BASE_SCHEMA

    yield

    data_def.SYSTEM_SCHEMA = old_system_schema
    data_def.BASE_SCHEMA = old_base_schema

    for key, value in old_types.items():
        base_types.__dict__[key] = value

    db.engine = old_engine


@pytest.fixture
def datadir():
    datadir = os.path.join(os.path.dirname(__file__), '../data')
    return datadir


@pytest.fixture
def fake_datadir():
    fake_datadir = os.path.join(os.path.dirname(__file__), 'data')
    return fake_datadir

import os.path

import pytest
import sqlalchemy
from unittest.mock import MagicMock

from magnate.savegame import base_types
from magnate.savegame import data_def
from magnate.savegame import db


def test_init_schema(datadir):
    db_items = len(db.__dict__)
    undefined_schema = []
    for name, value in db.__dict__.items():
        if value is None and name not in ('engine',):
            undefined_schema.append(name)

    db.init_schema(datadir)

    # Assert nothing was added
    assert len(db.__dict__) == db_items

    # Assert that all schema values have been filled
    for name in undefined_schema:
        print(name)
        assert db.__dict__[name] is not None


def test_init_schema_cached(datadir):
    db_items = len(db.__dict__)
    undefined_schema = []
    for name, value in db.__dict__.items():
        if value is None and name not in ('engine',):
            undefined_schema.append(name)

    db.init_schema(datadir)

    first_schema = {}
    for name, value in db.__dict__.items():
        first_schema[name] = value

    db.init_schema(datadir)
    # Assert nothing was added
    assert len(db.__dict__) == db_items

    # Assert that none of the schema values have changed
    for name, value in first_schema.items():
        assert db.__dict__[name] is value


def test_init_schema_partial(datadir):
    db_items = len(db.__dict__)
    undefined_schema = []
    for name, value in db.__dict__.items():
        if value is None and name not in ('engine',):
            undefined_schema.append(name)

    db.init_schema(datadir)

    first_schema = {}
    for name, value in db.__dict__.items():
        first_schema[name] = value

    # A table wasn't initialized globally yet
    db.CommodityCategory = None

    db.init_schema(datadir)
    # Assert nothing was added
    assert len(db.__dict__) == db_items

    # Assert that none of the schema values have changed
    for name, value in first_schema.items():
        assert db.__dict__[name] is value


def test_init_savegame(fake_datadir):
    engine = sqlalchemy.create_engine('sqlite://')
    game_data = data_def.load_data_definitions(fake_datadir)

    db.init_savegame(engine, game_data)

    Session = sqlalchemy.orm.sessionmaker(bind=engine)
    session = Session()

    systems = session.query(db.SystemData).all()
    assert len(systems) == 1
    assert systems[0].name == 'Test'
    assert len(systems[0].celestials) == 2
    assert frozenset((systems[0].celestials[0].name, systems[0].celestials[1].name)) == frozenset(('Primary', 'Friesland'))
    assert systems[0].celestials[0].locations[0].name == 'Solar Observation Station'
    assert systems[0].celestials[1].locations == []

    commodities = session.query(db.CommodityData).all()
    assert len(commodities) == 1
    assert commodities[0].name == 'Drugs'

    ships = session.query(db.ShipData).all()
    assert len(ships) == 1
    assert ships[0].name == 'ship'

    properties = session.query(db.PropertyData).all()
    assert len(properties) == 1
    assert properties[0].name == 'property'

    ship_parts = session.query(db.ShipPartData).all()
    assert len(ship_parts) == 2
    assert frozenset((ship_parts[0].name, ship_parts[1].name)) == frozenset(('add storage', 'take up space'))

    events = session.query(db.EventData).filter(db.EventData.msg == 'price lower').all()
    assert len(events) == 1
    assert events[0].adjustment == -5
    assert len(events[0].affects) == 2
    assert events[0].affects[0].categories == {base_types.CommodityType.food}
    assert events[0].affects[1].categories == {base_types.CommodityType.illegal, base_types.CommodityType.chemical}


def test_create_savegame():
    pass


def test_load_savegame_invalid():
    pass

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
"""
Persists a game to disk as a database.
"""
import os

from alembic.config import Config
from alembic import command
from sqlalchemy import create_engine
from sqlalchemy import Column, Enum, ForeignKey, Integer, String
from sqlalchemy import UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy_repr import RepresentableBase
from twiggy import log

from ..errors import MagnateInvalidSaveGame, MagnateNoSaveGame
from . import base_types
from . import data_def

# Stellar Magnate ships with certain static data in yaml files
# This data is loaded into a database whose schema is defined below
# When the game is updated, the data may be updated as well.  When this happens, we both ship
# updated data files and we ship alembic scripts to update existing save games to the new data.
# Alembic scripts allow us to transform the existing data

#
# Schema
#

Base = declarative_base(cls=RepresentableBase)
engine = None

# Convention: *Data classes contain static data loaded from this version of Stellar Magnate
# Many of these data classes have dynamic data associated with them.  These are stored in classes
# without the Data suffix.

# These are loaded by init_schema because they reference base_types that are loaded dynamically
CelestialData = None
LocationData = None
CommodityCategory = None
ConditionCategory = None


# TODO: take advantage of the following where it makes sense:
# association_proxy() => instead of having a list of records, have a list of strings
# relationship collection_class=set... have a set instead of a list
# relationship collection_class=attribute_mapped_collection... have a dict instead of a list


class SystemData(Base):
    __tablename__ = 'system'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    celestials = relationship('CelestialData', back_populates='system', order_by='CelestialData.orbit')


class Commodity(Base):
    __tablename__ = 'commodity'
    id = Column(Integer, primary_key=True)
    info_id = Column(Integer, ForeignKey('commodity_data.id'))
    info = relationship('CommodityData', backref='commodities')
    location_id = Column(Integer, ForeignKey('location.id'))
    location = relationship('LocationData', back_populates='commodities')
    price = Column(Integer, nullable=False)
    last_update = Column(Integer, nullable=False)
    __table_args__ = (UniqueConstraint('info_id', 'location_id', name='commodity_unique'),)


class CommodityData(Base):
    __tablename__ = 'commodity_data'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    mean_price = Column(Integer, nullable=False)
    standard_deviation = Column(Integer, nullable=False)
    depreciation_rate = Column(Integer, nullable=False)
    volume = Column(Integer, nullable=False)


class Ship(Base):
    __tablename__ = 'ship'
    id = Column(Integer, primary_key=True)
    info_id = Column(Integer, ForeignKey('ship_data.id'))
    info = relationship('ShipData', backref='ships')
    condition = Column(Integer, nullable=False)
    owner_id = Column(Integer, ForeignKey('character.id'), nullable=False)
    owner = relationship('Character', backref='ships')
    location_id = Column(Integer, ForeignKey('location.id'), nullable=False)
    location = relationship('Location', backref='ships')


class ShipData(Base):
    __tablename__ = 'ship_data'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    mean_price = Column(Integer, nullable=False)
    standard_deviation = Column(Integer, nullable=False)
    depreciation_rate = Column(Integer, nullable=False)
    storage = Column(Integer, nullable=False)
    weapon_mounts = Column(Integer, nullable=False)


class Cargo(Base):
    __tablename__ = 'cargo'
    id = Column(Integer, primary_key=True)
    ship_id = Column(Integer, ForeignKey('ship.id'))
    ship = relationship('Ship', backref='cargo')
    commodity_id = Column(Integer, ForeignKey('commodity_data.id'))
    quantity = Column(Integer, nullable=False)
    purchase_price = Column(Integer, nullable=False)
    purchase_date = Column(Integer, nullable=False)


class Property(Base):
    __tablename__ = 'property'
    id = Column(Integer, primary_key=True)
    info_id = Column(Integer, ForeignKey('property_data.id'))
    info = relationship('PropertyData', backref='properties')
    condition = Column(Integer, nullable=False)
    owner_id = Column(Integer, ForeignKey('character.id'), nullable=False)
    owner = relationship('Character', backref='properties')


class PropertyData(Base):
    __tablename__ = 'property_data'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    mean_price = Column(Integer, nullable=False)
    standard_deviation = Column(Integer, nullable=False)
    depreciation_rate = Column(Integer, nullable=False)
    storage = Column(Integer, nullable=False)


class ShipPart(Base):
    __tablename__ = 'ship_part'
    id = Column(Integer, primary_key=True)
    info_id = Column(Integer, ForeignKey('ship_part_data.id'))
    info = relationship('ShipPartData', backref='ship_parts')
    condition = Column(Integer, nullable=False)
    owner_id = Column(Integer, ForeignKey('character.id'), nullable=False)
    owner = relationship('Character', backref='properties')


class ShipPartData(Base):
    __tablename__ = 'ship_part_data'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    mean_price = Column(Integer, nullable=False)
    standard_deviation = Column(Integer, nullable=False)
    depreciation_rate = Column(Integer, nullable=False)
    storage = Column(Integer, nullable=False)


class EventData(Base):
    __tablename__ = 'event_data'
    id = Column(Integer, primary_key=True)
    msg = Column(String, nullable=False)
    adjustment = Column(Integer, nullable=False)


class _EventCondition(Base):
    __tablename__ = 'event_condition'
    event_id = Column(ForeignKey('event_data.id'), primary_key=True)
    event = relationship('EventData', backref='affects')
    condition_category_id = Column(ForeignKey('condition_category.id'), primary_key=True)
    condition_category = relationship('ConditionCategory', backref='affects')
    __table_args__ = (UniqueConstraint('event_id', 'condition_category_id', name='event_condition_unique'),)


class Character(Base):
    __tablename__ = 'character'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)


class World(Base):
    __tablename__ = 'world'
    id = Column(Integer, primary_key=True)
    time = Column(Integer, unique=True, nullable=False)


def init_schema(datadir):
    # We always initialize the base game types first to avoid chicken and egg problems attempting to
    # validate loading of other data and setting up the save game schema
    base_types.init_base_types(datadir)

    # Some of the schema depends on the base_types so create the remaining schema elements now that
    # base_types have been loaded

    global CelestialData
    class _CelestialData(Base):
        __tablename__ = 'celestial'
        id = Column(Integer, primary_key=True)
        name = Column(String, unique=True, nullable=False)
        orbit = Column(Integer, nullable=False)
        type = Column(Enum(base_types.CelestialType), nullable=False)
        system_id = Column(Integer, ForeignKey('system.id'), nullable=False)
        system = relationship('SystemData', back_populates='celestials')
    CelestialData = _CelestialData

    global LocationData
    class _LocationData(Base):
        __tablename__ = 'location'
        id = Column(Integer, primary_key=True)
        name = Column(String, unique=True, nullable=False)
        type = Column(Enum(base_types.LocationType), nullable=False)
        celestial_id = Column(Integer, ForeignKey('celestial.id'), nullable=False)
        celestial = relationship('SystemData', backref='locations')
        commodities = relationship('Commodity', back_populates='location', order_by='commodity.price')
    LocationData = _LocationData

    global CommodityCategory
    class _CommodityCategory(Base):
        __tablename__ = 'commodity_category'
        commodity_id = Column(ForeignKey('commodity.id'), primary_key=True)
        commodity = relationship('CommodityData', backref='types')
        category = Column(Enum(base_types.CommodityType), primary_key=True)
        __table_args__ = (UniqueConstraint('commodity_id', 'category', name='commodity_category_unique'),)
    CommodityCategory = _CommodityCategory

    # Events are a 2 dimensional array
    # An Event affects anything that satisfies a condition
    # Each condition contains a set of categories that all need to apply to the commodity
    global ConditionCategory
    class _ConditionCategory(Base):
        __tablename__ = 'condition_category'
        condition_id = Column(ForeignKey('event_conditon.id'), primary_key=True)
        condition = relationship('EventCondtion', backref='categories')
        category = Column(Enum(base_types.CommodityType), primary_key=True)
        __table_args__ = (UniqueConstraint('condition_id', 'category', name='condition_category_unique'),)
    ConditionCategory = _ConditionCategory


def init_savegame(engine, game_data):
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    for system in game_data['systems']:
        system_rec = SystemData(name=system['name'])
        session.add(system_rec)

        celestials_added = {}
        for celestial in system['celestials']:
            celestial_rec = CelestialData(name=celestial['name'],
                                          orbit=celestial['orbit'],
                                          type=celestial['type'],
                                         )
            session.add(celestial_rec)
            celestials_added[celestial['name']] = celestial_rec

        for location in system['locations']:
            location_rec = LocationData(name=location['name'],
                                        type=location['type'],
                                        celestial=celestials_added[location['celestial']],
                                       )
            session.add(location_rec)

        for commodity in system['commodities']:
            commodity_rec = CommodityData(name=commodity['name'],
                                          categories=commodity['categories'],
                                          mean_price=commodity['mean_price'],
                                          standard_deviation=commodity['standard_deviation'],
                                          depreciation_rate=commodity['depreciation_rate'],
                                          volume=commodity['volume'],
                                         )
            session.add(commodity_rec)

        for ship in game_data['ships']:
            ship_rec = ShipData(name=ship['name'],
                                mean_price=ship['mean_price'],
                                standard_deviation=ship['standard_deviation'],
                                depreciation_rate=ship['depreciation_rate'],
                                storage=ship['storage'],
                                weapon_mounts=ship['weapon_mounts'],
                               )
            session.add(ship_rec)

        for property_ in game_data['property']:
            property_rec = PropertyData(name=property_['name'],
                                        mean_price=property_['mean_price'],
                                        standard_deviation=property_['standard_deviation'],
                                        depreciation_rate=property_['depreciation_rate'],
                                        storage=property_['storage'],
                                       )
            session.add(property_rec)

        for parts in game_data['ship_parts']:
            parts_rec = ShipPartData(name=parts['name'],
                                     mean_price=parts['mean_price'],
                                     standard_deviation=parts['standard_deviation'],
                                     depreciation_rate=parts['depreciation_rate'],
                                     storage=parts['storage'],
                                    )
            session.add(parts_rec)

        for event in game_data['events']:
            event_rec = EventData(msg=event['msg'],
                                  adjustment=event['adjustment'],
                                  affects=event['affects'],
                                 )
            session.add(event_rec)


def load_savegame(savegame, datadir):
    if not os.path.exists(savegame):
        raise MagnateNoSaveGame(f'{savegame} does not point to a file')

    global engine

    savegame_uri = f'sqlite://{savegame}'
    try:
        engine = create_engine(savegame_uri)
    except Exception:
        log.trace('error').name('GameSetup').fields(savegame=savegame_uri).error('Savegame uri was invalid')
        raise MagnateInvalidSaveGame(f'"{savegame_uri}" was malformed')

    # All save games get upgraded to the latest version on load
    '''
    alembic_cfg = Config(os.path.join(datadir, "alembic.ini"))
    alembic_cfg.set_main_option('sqlalchemy.url', savegame)
    try:
        alembic.upgrade(alembic_cfg)
    except Exception as e:
        log.trace('error').name('GameSetup').fields(savegame=savegame).error('Savegame file was invalid')
        raise MagnateInvalidSaveGame(f'{savegame} is not a valid save file')
    '''

    return engine


def create_savegame(savegame, datadir):
    """Create a new savegame file"""

    global engine

    savegame_uri = f'sqlite:///{savegame}'
    try:
        engine = create_engine(savegame_uri)
    except Exception as e:
        log.trace('error').name('GameSetup').fields(savegame=savegame_uri).error('Savegame uri was invalid')
        raise MagnateInvalidSaveGame(f'"{savegame_uri}" was malformed')

    game_data = data_def.load_data_definitions(datadir)
    init_savegame(engine, game_data)

    return engine

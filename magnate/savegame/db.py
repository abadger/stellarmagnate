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
import sqlalchemy.exc
from sqlalchemy import create_engine
from sqlalchemy import Column, Enum, ForeignKey, Integer, String
from sqlalchemy import UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy_repr import RepresentableBase

from ..errors import MagnateInvalidSaveGame, MagnateNoSaveGame
from ..logging import log
from . import base_types
from . import data_def


mlog = log.fields(mod=__name__)

# Stellar Magnate ships with certain static data in yaml files
# This data is loaded into a database whose schema is defined below
# When the game is updated, the data may be updated as well.  When this happens, we both ship
# updated data files and we ship alembic scripts to update existing save games to the new data.
# Alembic scripts allow us to transform the existing data

#
# Schema
#

Base = None  # pylint: disable=invalid-name
engine = None

# Convention: *Data classes contain static data loaded from this version of Stellar Magnate
# Many of these data classes have dynamic data associated with them.  These are stored in classes
# without the Data suffix.

class PricedItem:
    """
    Mixin for any Schema class which can be bought and sold
    """
    name = Column(String, unique=True, nullable=False)
    mean_price = Column(Integer, nullable=False)
    standard_deviation = Column(Integer, nullable=False)
    depreciation_rate = Column(Integer, nullable=False)


# All Schemas are loaded dynamically so we can also clear and reload them
SCHEMA_NAMES = ('SystemData', 'CelestialData', 'LocationData', 'Commodity', 'CommodityData',
                'CommodityCategory', 'Ship', 'ShipData', 'Cargo', 'Property', 'PropertyData',
                'ShipPart', 'ShipPartData', 'EventData', 'EventCondition', 'ConditionCategory',
                'Player', 'World',)


# Give the Schemas an initial value of None
m_globals = globals()
for name in SCHEMA_NAMES:
    m_globals[name] = None


def init_schema(datadir):
    """
    Initialize the dynamic pieces of our save game format's schema

    The dynamic pieces require that base_types have been initialized first as they limit certain
    fields to the base_type values

    :datadir: Directory for Stellar Magnate's data so that base_type data can be loaded.
    """
    flog = mlog.fields(func='init_schema')
    flog.fields(datadir=datadir).debug('Entered init_schema')

    # We always initialize the base game types first to avoid chicken and egg problems attempting to
    # validate loading of other data and setting up the save game schema
    base_types.init_base_types(datadir)

    # Some of the schema depends on the base_types so create the remaining schema elements now that
    # base_types have been loaded.
    # Only create them if they haven't already been created
    # TODO: take advantage of the following where it makes sense:
    # association_proxy() => instead of having a list of records, have a list of strings
    # relationship collection_class=set... have a set instead of a list
    # relationship collection_class=attribute_mapped_collection... have a dict instead of a list

    m_globals = globals()
    # pylint: disable=too-few-public-methods
    for name in SCHEMA_NAMES:
        if m_globals[name] is None:
            break
    else:
        flog.debug('Schema already loaded, returning without changes')
        return

    flog.debug('Defining Schema')
    global Base
    Base = declarative_base(cls=RepresentableBase)

    class SystemData(Base):  # pylint: disable=unused-variable
        """
        Static data about a stellar system

        :name: Name of the Stellar System
        :celestials: The celestial bodies that exist in this system
        """
        __tablename__ = 'system'
        id = Column(Integer, primary_key=True)
        name = Column(String, unique=True, nullable=False)
        celestials = relationship('CelestialData', back_populates='system',
                                  order_by='CelestialData.orbit')

    class CelestialData(Base):  # pylint: disable=unused-variable
        """
        Data about Celestial Bodies
        :name: Name of the body
        :orbit: Position from the system's primary
        :type: Type of the celestial body
        :system: System in which this celestial body lives
        :locations: Locations which exist on this Celestial body
        """
        __tablename__ = 'celestial_data'
        id = Column(Integer, primary_key=True)
        name = Column(String, unique=True, nullable=False)
        orbit = Column(Integer, nullable=False)
        type = Column(Enum(base_types.CelestialType), nullable=False)
        system_id = Column(Integer, ForeignKey('system.id'), nullable=False)
        system = relationship('SystemData', back_populates='celestials')

    class LocationData(Base):  # pylint: disable=unused-variable
        """
        Data about Locations that a Ship can land on

        :name: Name of the Location
        :type: LocationType of the location
        :celestial: Celestial body that the Location is associated with
        :commodities: Commodities available for sale at the Location
        :ships: Ships currently present at this Location
        """
        __tablename__ = 'location_data'
        id = Column(Integer, primary_key=True)
        name = Column(String, unique=True, nullable=False)
        type = Column(Enum(base_types.LocationType), nullable=False)
        celestial_id = Column(Integer, ForeignKey('celestial_data.id'), nullable=False)
        celestial = relationship('CelestialData', backref='locations')
        commodities = relationship('Commodity', back_populates='location',
                                   order_by='commodity.c.price')

    class Commodity(Base):  # pylint: disable=unused-variable
        """
        Data about an item that is presently for sale in a market

        :info: Contains the fundamental data about this Commodity
        :location: The location at which this Commodity is for sale
        :price: Current price of the Commodity at this location
        :last_update: Last time the price of this Commodity was updated
        """
        __tablename__ = 'commodity'
        id = Column(Integer, primary_key=True)
        info_id = Column(Integer, ForeignKey('commodity_data.id'))
        info = relationship('CommodityData', backref='commodities')
        location_id = Column(Integer, ForeignKey('location_data.id'))
        location = relationship('LocationData', back_populates='commodities')
        price = Column(Integer, nullable=False)
        last_update = Column(Integer, nullable=False)
        __table_args__ = (UniqueConstraint('info_id', 'location_id', name='commodity_unique'),)

    class CommodityData(PricedItem, Base):  # pylint: disable=unused-variable
        """
        Fundamental market data about a commodity

        :name: Name of the commodity
        :mean_price: The average price of this commodity
        :standard_deviation: One standard deviation of the price data
        :depreciation_rate: Rate at which the Commodity depreciates in value.
        :volume: How much space one unit of the item takes up
        :categories: Set of categories that the commodity belongs to
        :commodities: List of the actual instances of this commodity for sale
        """
        __tablename__ = 'commodity_data'
        id = Column(Integer, primary_key=True)
        volume = Column(Integer, nullable=False)
        categories = relationship('CommodityCategory', back_populates='commodity',
                                  collection_class=set)

    class CommodityCategory(Base):  # pylint: disable=unused-variable
        """
        CommodityType that a Commodity belongs to

        :commodity: Commodity which has this as a category
        :category: CommodityType for the Commodity
        """
        __tablename__ = 'commodity_category'
        commodity_id = Column(ForeignKey('commodity_data.id'), primary_key=True)
        commodity = relationship('CommodityData', back_populates='categories')
        category = Column(Enum(base_types.CommodityType), primary_key=True)
        __table_args__ = (UniqueConstraint('commodity_id', 'category',
                                           name='commodity_category_unique'),)

    class Ship(Base):  # pylint: disable=unused-variable
        """
        Data about a specific instance of a Ship

        :info: Links to the fundamental data about the Ship
        :condition: How damaged the Ship is
        :owner: The owner of the Ship
        :location: Where the Ship is currently located
        :ship_parts: List of ship_parts that are installed onto this Ship
        :cargo: List of all Commodities currently stored on the Ship
        """
        __tablename__ = 'ship'
        id = Column(Integer, primary_key=True)
        info_id = Column(Integer, ForeignKey('ship_data.id'))
        info = relationship('ShipData', backref='ships')
        condition = Column(Integer, nullable=False)
        owner_id = Column(Integer, ForeignKey('player.id'), nullable=False)
        owner = relationship('Player', backref='ships')
        location_id = Column(Integer, ForeignKey('location_data.id'), nullable=False)
        location = relationship('LocationData', backref='ships')

    class ShipData(PricedItem, Base):  # pylint: disable=unused-variable
        """
        Fundamental data about all Ships of a class

        :name: Name of the ship type
        :ships: List of all ships of this type in existence
        :mean_price: The average price of this Ship
        :standard_deviation: One standard deviation of the price data
        :depreciation_rate: Rate at which the Ship depreciates in value.
        :storage: How much cargo volume exists on this ship
        :weapon_mounts: How many weapons this ship can accept
        """
        __tablename__ = 'ship_data'
        id = Column(Integer, primary_key=True)
        storage = Column(Integer, nullable=False)
        weapon_mounts = Column(Integer, nullable=False)

    class Cargo(Base):  # pylint: disable=unused-variable
        """
        Commodities that are owned by a Player

        :ship: Ship that this cargo is presently stored in
        :commodity: Commodity that is being stored
        :quantity: Amount of the Cargo that is being stored
        :purchase_price: Amount that the Player purchased the Cargo for
        :purchase_date: Timestamp when the Cargo was purchased
        """
        __tablename__ = 'cargo'
        id = Column(Integer, primary_key=True)
        ship_id = Column(Integer, ForeignKey('ship.id'))
        ship = relationship('Ship', backref='cargo')
        commodity_id = Column(Integer, ForeignKey('commodity_data.id'))
        commodity = relationship('CommodityData')
        quantity = Column(Integer, nullable=False)
        purchase_price = Column(Integer, nullable=False)
        purchase_date = Column(Integer, nullable=False)

    class Property(Base):  # pylint: disable=unused-variable
        """
        Instance of an owned Property

        :info: Link to the generic data about any property of this type
        :condition: Any degradation of the Property
        :owner: Link to the Player who owns the Property
        """
        __tablename__ = 'property'
        id = Column(Integer, primary_key=True)
        info_id = Column(Integer, ForeignKey('property_data.id'))
        info = relationship('PropertyData', backref='properties')
        condition = Column(Integer, nullable=False)
        owner_id = Column(Integer, ForeignKey('player.id'), nullable=False)
        owner = relationship('Player', backref='properties')

    class PropertyData(PricedItem, Base):  # pylint: disable=unused-variable
        """
        Data about all Properties of a certain type

        :name: The name of this property
        :mean_price: Average price of the part
        :standard_deviation: One standard deviation of the price data
        :depreciation_rate: Rate at which the Commodity depreciates in value.
        :storage: How much storage this Property has.
        :properties: List of properties that are of this type
        """
        __tablename__ = 'property_data'
        id = Column(Integer, primary_key=True)
        storage = Column(Integer, nullable=False)

    class ShipPart(Base):  # pylint: disable=unused-variable
        """
        Instance of ShipPart which is installed in a Ship

        :info: Information about the base ShipPart
        :condition: Amount of damage this part has suffered
        :ship: Ship that this part is installed into
        """
        __tablename__ = 'ship_part'
        id = Column(Integer, primary_key=True)
        info_id = Column(Integer, ForeignKey('ship_part_data.id'))
        info = relationship('ShipPartData', backref='ship_parts')
        condition = Column(Integer, nullable=False)
        ship_id = Column(Integer, ForeignKey('ship.id'))
        ship = relationship('Ship', backref='ship_parts')

    class ShipPartData(PricedItem, Base):  # pylint: disable=unused-variable
        """
        Part that can be installed on a Ship

        :name: Name of the ship type
        :mean_price: Average price of the part
        :standard_deviation: One standard deviation of the price data
        :depreciation_rate: Rate at which the Commodity depreciates in value.
        :storage: How much space this part adds to the ship.  Negative values subtract storage from the
            Ship.
        :categories: Set of categories that the commodity belongs to
        :ship_parts: List of this ship parts which are installed into ships
        """
        __tablename__ = 'ship_part_data'
        id = Column(Integer, primary_key=True)
        storage = Column(Integer, nullable=False)

    class EventData(Base):  # pylint: disable=unused-variable
        """
        An Event that affects the price of Commodities

        :msg: Event description to tell the user what has happened
        :adjustment: The amount a price will rise or fall in response to the Event
        :affects: The EventConditions that a Commodity must meet for its price to be affected by this
            Event
        """
        __tablename__ = 'event_data'
        id = Column(Integer, primary_key=True)
        msg = Column(String, nullable=False)
        adjustment = Column(Integer, nullable=False)

    class EventCondition(Base):  # pylint: disable=unused-variable
        """
        Condition for the event

        :event: The Event for which this is a condition
        :categories: Records in the ConditionCategory table which relate the CommodityTypes that are
            affected by the Event
        """
        __tablename__ = 'event_condition'
        id = Column(Integer, primary_key=True)
        event_id = Column(ForeignKey('event_data.id'))
        event = relationship('EventData', backref='affects')
        _categories = relationship('ConditionCategory', back_populates='condition',
                                  collection_class=set)
        categories = association_proxy('_categories', 'category')

    class ConditionCategory(Base):  # pylint: disable=unused-variable
        """
        A CommodityType to match for Events

        Events apply to any satisfied EventConditions.  An individual EventCondition is satisfied
        when all of the CommodityTypes it references match.  ConditionCategory holds those
        CommodityTypes.

        :condition: The EventCondition to which this Category belongs
        :category: The ConmmodityType that this references.
        """
        __tablename__ = 'condition_category'
        id = Column(Integer, primary_key=True)
        condition_id = Column(ForeignKey('event_condition.id'))
        condition = relationship('EventCondition', back_populates='_categories')
        category = Column(Enum(base_types.CommodityType))
        __table_args__ = (UniqueConstraint('condition_id', 'category',
                                           name='condition_category_unique'),)

    class Player(Base):  # pylint: disable=unused-variable
        """
        Player data

        :name: Name of the player
        :password: Password of the player
        :properties: Properties owned by the Player
        :ships: Ships owned by the Player
        :cash: Amount of cash the Player has on their person
        """
        __tablename__ = 'player'
        id = Column(Integer, primary_key=True)
        name = Column(String, unique=True, nullable=False)
        password = Column(String, nullable=False)
        cash = Column(Integer, nullable=False)

    class World(Base):  # pylint: disable=unused-variable
        """
        Global information about the world

        :time: Number of ticks since the world started
        """
        __tablename__ = 'world'
        id = Column(Integer, primary_key=True)
        time = Column(Integer, unique=True, nullable=False)

    # pylint: enable=too-few-public-methods

    flog.debug('Saving dynamic Schema to the global level')
    f_locals = locals()
    for name in SCHEMA_NAMES:
        m_globals[name] = f_locals[name]


def _init_systems(session, systems):
    """
    Initialize system information in the savegame

    :session: Database session to add to
    :systems: Data structure holding information about systems
    """
    for system in systems:
        system_rec = SystemData(name=system['name'])
        session.add(system_rec)

        celestials_added = {}
        for celestial in system['celestials']:
            celestial_rec = CelestialData(name=celestial['name'],  # pylint: disable=not-callable
                                          orbit=celestial['orbit'],
                                          type=celestial['type'],
                                          system=system_rec,)
            session.add(celestial_rec)
            celestials_added[celestial['name']] = celestial_rec

        for location in system['locations']:
            location_rec = LocationData(name=location['name'],  # pylint: disable=not-callable
                                        type=location['type'],
                                        celestial=celestials_added[location['celestial']],)
            session.add(location_rec)

        for commodity in system['commodities']:
            commodity_rec = CommodityData(name=commodity['name'],
                                          mean_price=commodity['mean_price'],
                                          standard_deviation=commodity['standard_deviation'],
                                          depreciation_rate=commodity['depreciation_rate'],
                                          volume=commodity['volume'],)
            session.add(commodity_rec)
            for category in commodity['categories']:
                # pylint: disable=not-callable
                commodity_cat = CommodityCategory(category=category,
                                                  commodity=commodity_rec)
                # pylint: enable=not-callable
                session.add(commodity_cat)


def _init_ships(session, ships):
    """
    Initialize ship information in the savegame

    :session: Database session to add to
    :ships: Data structure holding information about available ship types
    """
    for ship in ships:
        ship_rec = ShipData(name=ship['name'],
                            mean_price=ship['mean_price'],
                            standard_deviation=ship['standard_deviation'],
                            depreciation_rate=ship['depreciation_rate'],
                            storage=ship['storage'],
                            weapon_mounts=ship['weapon_mounts'],)
        session.add(ship_rec)


def _init_property(session, properties):
    """
    Initialize property information in the savegame

    :session: Database session to add to
    :properties: Data structure holding information about available types of Property
    """
    for property_ in properties:
        property_rec = PropertyData(name=property_['name'],
                                    mean_price=property_['mean_price'],
                                    standard_deviation=property_['standard_deviation'],
                                    depreciation_rate=property_['depreciation_rate'],
                                    storage=property_['storage'],)
        session.add(property_rec)


def _init_parts(session, ship_parts):
    """
    Initialize ship_parts information in the savegame

    :session: Database session to add to
    :ship_parts: Data structure holding information about available ship_parts
    """
    for parts in ship_parts:
        if 'storage' not in parts:
            parts['storage'] = -parts['volume']

        parts_rec = ShipPartData(name=parts['name'],
                                 mean_price=parts['mean_price'],
                                 standard_deviation=parts['standard_deviation'],
                                 depreciation_rate=parts['depreciation_rate'],
                                 storage=parts['storage'],)
        session.add(parts_rec)


def _init_events(session, events):
    """
    Initialize event information in the savegame

    :session: Database session to add to
    :events: Data structure holding information about available events
    """
    for event in events:
        event_rec = EventData(msg=event['msg'],
                              adjustment=event['adjustment'],)
        session.add(event_rec)

        for condition in event['affects']:
            condition_rec = EventCondition(event=event_rec)
            session.add(condition_rec)
            # pylint: disable=not-callable
            if isinstance(condition, list):
                # pylint: enable=not-callable
                for condition_cat in condition:
                    # pylint: disable=not-callable
                    condition_cat_rec = ConditionCategory(category=condition_cat,
                                                          condition=condition_rec)
                    # pylint: enable=not-callable
                    session.add(condition_cat_rec)
            else:
                condition_cat_rec = ConditionCategory(category=condition,
                                                      condition=condition_rec)
                # pylint: enable=not-callable
                session.add(condition_cat_rec)


def init_savegame(engine, game_data):
    """
    Initialize a savegame file from static game data loaded from the disk

    :arg engine: SQLAlchemy engine refering to the savegame file
    :arg game_data: Static game data that shipped with this version of the game
    """
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)  # pylint: disable=invalid-name
    session = Session()

    _init_systems(session, game_data['systems'])
    _init_ships(session, game_data['ships'])
    _init_property(session, game_data['property'])
    _init_parts(session, game_data['ship_parts'])
    _init_events(session, game_data['events'])

    session.commit()


def create_savegame(savegame, datadir):
    """Create a new savegame file"""
    flog = mlog.fields(func='create_savegame')
    flog.fields(savegame=savegame, datadir=datadir).debug('Entering create_savegame')

    global engine

    savegame_uri = f'sqlite:///{savegame}'
    flog.debug('Associating savegame with global `engine` var')
    engine = create_engine(savegame_uri)

    game_data = data_def.load_data_definitions(datadir)
    init_savegame(engine, game_data)

    flog.debug('Returning engine')
    return engine


def load_savegame(savegame, datadir):
    """
    Load a game from a savegame file

    This also upgrades the savegame file if it is for an older version.

    :arg savegame: savegame filename to attempt to load
    :arg datadir: Directory where Stellar Magnates data files are located.
        The Alembic files used to upgrade savegames to a new version are located here.
    :raises MagnateNoSaveGame: If the savegame does not exist
    :raises MagnateInvalidSaveGame: If the savegame exists but cannot be processed.
    :returns: The SQLAlchemy engine referencing the file
    """
    flog = log.fields(func='load_savegame')
    flog.fields(savegame=savegame, datadir=datadir).debug('Entering load_savegame')

    if not os.path.exists(savegame):
        raise MagnateNoSaveGame(f'{savegame} does not point to a file')

    global engine

    savegame_uri = f'sqlite:///{savegame}'
    flog.debug('Associating savegame with global `engine` var')
    engine = create_engine(savegame_uri)

    # All save games get upgraded to the latest version on load
    '''
    alembic_cfg = Config(os.path.join(datadir, "alembic.ini"))
    alembic_cfg.set_main_option('sqlalchemy.url', savegame)
    try:
        alembic.upgrade(alembic_cfg)
    except Exception as e:
        flog.trace('error').fields(savegame=savegame).error('Savegame file was invalid')
        raise MagnateInvalidSaveGame(f'{savegame} is not a valid save file')
    '''

    flog.debug('Returning engine')
    return engine

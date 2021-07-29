""" 
Module for everything gamemap related.
Currently, gamemap is understood as the floor the actors can do actions
"""

from __future__ import annotations
from typing import Iterable, Iterator, Optional, TYPE_CHECKING

import numpy as np # type: ignore
from tcod.console import Console

from entity import Actor, Item
import tile_types

if TYPE_CHECKING:
    from engine import Engine
    from entity import Entity

class GameMap:
    """
    Main class of GameMap. 
    Constains information of the current floor
    """
    def __init__(
        self, engine: Engine, width: int, height: int, entities: Iterable[Entity] = ()
    ):
        """
        Initialize the map
        Please note that Iterable[Entity] for entities turns into self.entities as a set

        :param engine: Engine which will be used by/to map?
        :type engine: Engine
        :param width: Width of the map, as in, x-axis max size
        :type width: int
        :param height: Height of the map, as in, y-axis max size
        :type height: int
        :param entities: Entities which exist (or should exist?) in the map, defaults to (), since it will be instanciated to self.entities as a Set
        :type entities: Iterable[Entity], optional
        """
        self.engine = engine
        self.width, self.height = width, height
        self.entities = set(entities)
        self.tiles = np.full((width, height), fill_value=tile_types.wall, order="F")

        self.visible = np.full(
            (width, height), fill_value=False, order="F"
        ) #tiles the player can currently see
        self.explored = np.full(
            (width, height), fill_value=False, order="F"
        ) #tiles that have been seen

        self.downstairs_location = (0, 0)

    @property
    def gamemap(self) -> GameMap:
        """Returns itself

        :return: Self
        :rtype: GameMap
        """
        return self
    
    @property
    def actors(self) -> Iterator[Actor]:
        """Returns yield from all actors in the map
        https://stackoverflow.com/questions/9708902/in-practice-what-are-the-main-uses-for-the-new-yield-from-syntax-in-python-3
        https://www.python.org/dev/peps/pep-0380/

        :yield: Returns all actors in the map
        :rtype: Iterator[Actor]
        """
        yield from (
            entity
            for entity in self.entities
            if (isinstance(entity, Actor) and entity.is_alive)
        )

    @property
    def items(self) -> Iterator[Item]:
        """Returns yield from all items in the map
        https://stackoverflow.com/questions/9708902/in-practice-what-are-the-main-uses-for-the-new-yield-from-syntax-in-python-3
        https://www.python.org/dev/peps/pep-0380/

        :yield: Returns all items in the map
        :rtype: Iterator[Item]
        """
        yield from (entity for entity in self.entities if isinstance(entity, Item))

    def get_blocking_entity_at_location(
        self, location_x: int, location_y: int
    ) -> Optional[Entity]:
        """Entities can only exist one per coordinate
        Se we check if there is any blocking entity at the target location

        :param location_x: x coordinate to check
        :type location_x: int
        :param location_y: y coordinate to check
        :type location_y: int
        :return: The blocking entity at the target location, or None if there is no blocking entity
        :rtype: Optional[Entity]
        """
        for entity in self.entities:
            if (
                entity.blocks_movement and 
                entity.x == location_x and 
                entity.y == location_y
            ):
                return entity
        
        return None
        
    def get_actor_at_location(self, x: int, y: int) -> Optional[Actor]:
        """Actors can only exist one per coordinate
        Check if there is one at location and returns it

        :param x: x coodinate to check
        :type x: int
        :param y: y coordinate to check
        :type y: int
        :return: Actor at the target location, or None if there is no actor
        :rtype: Optional[Actor]
        """
        for actor in self.actors:
            if(actor.x == x and actor.y == y):
                return actor

        return None
    
    def in_bounds(self, x: int, y: int) -> bool:
        """Return true if x and y are inside of the bounds of this map

        :param x: x coordinate to check
        :type x: int
        :param y: y coordinate to check
        :type y: int
        :return: True if x and y are inside of the bounds of this map
        :rtype: bool
        """
        return 0 <= x < self.width and 0 <= y < self.height

    def render(self, console: Console) -> None:
        """
        Will render all entities in the map to the console
        Initially it renders the maps using the tiles
        Then it orders the entities to render

        :param console: Console to render to
        :type console: Console
        """
        console.tiles_rgb[0 : self.width, 0 : self.height] = np.select(
            condlist=[self.visible, self.explored],
            choicelist=[self.tiles["light"], self.tiles["dark"]],
            default=tile_types.SHROUD,
        )

        entities_sorted_for_rendering = sorted(
            self.entities, key=lambda x: x.render_order.value
        )

        for entity in entities_sorted_for_rendering:
            #only print entities that are visible
            if(self.visible[entity.x, entity.y]):
                console.print(
                    entity.x, entity.y, entity.char, fg=entity.color
                )

class GameWorld:
   """
   Holds the settings for the GameMap, and generates new maps when moving down the stairs.
   """

   def __init__(
       self,
       *,
       engine: Engine,
       map_width: int,
       map_height: int,
       max_rooms: int,
       room_min_size: int,
       room_max_size: int,
       current_floor: int = 0
   ):
       """
       Intialization of the GameWorld which will hold the GameMaps
       Most of its parameters are set for the procedural map generator

       :param engine: Engine that will get the gamemap
       :type engine: Engine
       :param map_width: Width of the map, as in x-axis maximum
       :type map_width: int
       :param map_height: Height of the map, as in y-axis maximum
       :type map_height: int
       :param max_rooms: Maximum of rooms in map
       :type max_rooms: int
       :param room_min_size: Minimum room size
       :type room_min_size: int
       :param room_max_size: Maximum room size
       :type room_max_size: int
       :param current_floor: Current floor, defaults to 0
       :type current_floor: int, optional
       """
       self.engine = engine

       self.map_width = map_width
       self.map_height = map_height

       self.max_rooms = max_rooms

       self.room_min_size = room_min_size
       self.room_max_size = room_max_size

       self.current_floor = current_floor

   def generate_floor(self) -> None:
       """
       Will generate a new floor and place it in the engine
       """
       from procgen import generate_dungeon

       self.current_floor += 1

       self.engine.game_map = generate_dungeon(
           max_rooms=self.max_rooms,
           room_min_size=self.room_min_size,
           room_max_size=self.room_max_size,
           map_width=self.map_width,
           map_height=self.map_height,
           engine=self.engine,
       )
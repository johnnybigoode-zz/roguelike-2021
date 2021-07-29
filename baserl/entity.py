"""
Defines the entity 'abstract' class?
And a few of the initial implementations of the class
"""
from  __future__ import annotations

import copy
import math
from typing import Optional, Tuple, Type, TypeVar, TYPE_CHECKING, Union
from render_order import RenderOrder

if(TYPE_CHECKING):
    from components.ai import BaseAI
    from components.consumable import Consumable
    from components.equipment import Equipment
    from components.equippable import Equippable
    from components.fighter import Fighter
    from components.inventory import Inventory
    from components.level import Level
    from game_map import GameMap

T = TypeVar("T", bound="Entity")

class Entity:
    """This is a thing that exists in our gameworld
    Using the Entity Component System model, an entity should be data
    Behavior should not be part of the entity itself, but rather be
    a component that is part of the entity defined by :class:`BaseComponent`

    :param parent: Whose gamemap this entity is on
    :type parent: GameMap, Optional
    :param x: x coordinate of the entity
    :type x: int
    :param y: y coordinate of the entity
    :type y: int
    :param char:  Character to represent the entity
    :type str: str
    :param color: Color of the entity
    :type color: Tuple[int, int, int]
    :param name: Name of the entity
    :type name: str
    :param blocks_movement: If entity blocks movement
    :type blocks_movement: bool
    :param render_order: What order to render the entity
    :type render_order: RenderOrder
    """
    parent: Union[GameMap, Inventory]

    def __init__(
        self, 
        parent: Optional[GameMap] = None,
        x:int = 0, 
        y:int = 0, 
        char: str = "?",
        color: Tuple[int,int,int] = (255, 255, 255),
        name:str = "<Unnamed>",
        blocks_movement: bool = False,
        render_order: RenderOrder = RenderOrder.CORPSE,
    ):
        """Maybe I'm putting comments in the wrong places

        :param parent: Whose gamemap this entity is on
        :type parent: Optional[GameMap], optional
        :param x: x coordinate of the entity
        :type x: int
        :param y: y coordinate of the entity
        :type y: int
        :param char:  Character to represent the entity
        :type str: str
        :param color: Color of the entity
        :type color: Tuple[int, int, int]
        :param name: Name of the entity
        :type name: str
        :param blocks_movement: If entity blocks movement
        :type blocks_movement: bool
        :param render_order: What order to render the entity
        :type render_order: RenderOrder
        """
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        self.name = name
        self.blocks_movement =  blocks_movement
        self.render_order = render_order
        if parent:
            # if parent inst provided now, then it will be set later
            self.parent = parent
            parent.entities.add(self) #excuse me what

    @property
    def gamemap(self) -> GameMap:
        """Returns the parent's gamemap

        :return: GameMap that this entity existis in
        :rtype: GameMap
        """
        return self.parent.gamemap

    def spawn(self: T, gamemap: GameMap, x: int, y: int) -> T:
        """Spawn a copy of this instance at the given location at GameMap

        :param self: I don't understand this part of the code
        :type self: T = TypeVar("T", bound="Entity")
        :param gamemap: Gamemap to spawn the entity in
        :type gamemap: GameMap
        :param x: x coordinate of the entity
        :type x: int
        :param y: y coordinate of the entity
        :type y: int
        :return: same as self : T = TypeVar("T", bound="Entity")
        :rtype: T
        """
        clone = copy.deepcopy(self)
        clone.x = x
        clone.y = y
        clone.parent  = gamemap
        gamemap.entities.add(clone)
        return clone
    
    def place(self, x:int, y:int, gamemap: Optional[GameMap] = None) -> None:
        """Use this when you wish to move a entity across GameMaps
        It will remove itself from its parents gamemap and add it to the new gamemap

        :param x: x coordinate of the entity
        :type x: int
        :param y: y coordinate of the entity
        :type y: int
        :param gamemap: Gamemap to place spawned entity in, defaults to None
        :type gamemap: Optional[GameMap], optional
        """
        self.x = x
        self.y = y
        if gamemap:
            if hasattr(self, "parent"): #possibily unitianilziaded
                self.parent.entities.remove(self)
            self.parent = gamemap
            gamemap.entities.add(self)

    def distance(self, x: int, y:int ) -> float:
        """Calculates distance between self and x,y coordinate using Pythagorean Theorem

        :param x: x coordinate of the entity
        :type x: int
        :param y: y coordinate of the entity
        :type y: int
        :return: distance between self and x,y coordinate
        :rtype: float
        """
        return math.sqrt((x - self.x) ** 2 + (y - self.y) ** 2)

    def move(self, dx: int, dy: int) -> None:
        """Move the entity by the given amount

        :param dx: Delta x to move by
        :type dx: int
        :param dy: Delta y to move by
        :type dy: int
        """

        self.x += dx
        self.y += dy
        
class Actor(Entity):
    """Class used to represent actors within our world
    Check entity_factories for some implementation examples
    Things like enemies, players are actors
    It's a subclass of entity so you can use the entity component system
    (need to validate this, python oop things are not clear as Java)
    """
    def __init__(
        self, 
        *,
        x: int = 0,
        y: int = 0,
        char: str = "?",
        color: Tuple[int, int, int] = (255, 255, 255),
        name: str = "<Unanamed>", 
        ai_cls: Type[BaseAI],
        equipment: Equipment,
        fighter: Fighter,
        inventory: Inventory,
        level: Level,
    ):
        """Initializes the class

        :param x: current X coordinate, defaults to 0
        :type x: int, optional
        :param y: current Y coordinate, defaults to 0
        :type y: int, optional
        :param char: Symbol that represents actor, defaults to "?"
        :type char: str, optional
        :param color: Color for the actor, defaults to (255, 255, 255)
        :type color: Tuple[int, int, int], optional
        :param name: Actor's name, defaults to "<Unanamed>"
        :type name: str, optional
        :param blocks_movement: If actor blocks movement, defaults to True
        :type blocks_movement: bool
        :param render_order:  What order to render the actor, defaults to RenderOrder.ACTOR
        :type render_order: RenderOrder
        """
        super().__init__(
            x=x,
            y=y,
            char=char,
            color=color,
            name=name,
            blocks_movement=True,
            render_order=RenderOrder.ACTOR,
        )

        self.ai: Optional[BaseAI] = ai_cls(self)

        self.equipment: Equipment = equipment
        self.equipment.parent = self

        self.fighter = fighter
        self.fighter.parent = self

        self.inventory = inventory
        self.inventory.parent = self

        self.level = level
        self.level.parent = self

    @property
    def is_alive(self) -> bool:
        """Checks if actor is alive

        :return: True if actor is alive, False otherwise
        :rtype: bool
        """
        return bool(self.ai)

class Item(Entity):
    """Class used to define items in our world
    Check entity_factories for some implementation examples    
    """
    def __init__(
        self, 
        *,
        x: int = 0, 
        y: int = 0, 
        char: str = "?", 
        color: Tuple[int, int, int] = (255, 255, 255), 
        name: str = "<Unnamed>", 
        consumable: Optional[Consumable] = None,
        equippable: Optional[Equippable] = None,
    ):
        """Initialization method

        :param self: should this even be documented
        :type ?: self
        :param *: Not sure why this is here
        :type *: Please check
        :param x: Current x coordinate, defaults to 0
        :type x: int, optional
        :param y: Current y coordinate, defaults to 0
        :type y: int, optional
        :param char: Char used to represent item, defaults to "?"
        :type char: str, optional
        :param color: Color used for item, defaults to (255, 255, 255)
        :type color: Tuple[int, int, int], optional
        :param name: Item's name, defaults to "<Unnamed>"
        :type name: str, optional
        :param blocks_movement: If actor blocks movement, defaults to True
        :type blocks_movement: bool
        :param render_order:  What order to render the actor, defaults to RenderOrder.ACTOR
        :type render_order: RenderOrder
        """
        super().__init__(
            x=x, 
            y=y, 
            char=char, 
            color=color, 
            name=name, 
            blocks_movement=False, 
            render_order=RenderOrder.ITEM
        )

        self.consumable = consumable
        
        if self.consumable:
            self.consumable.parent = self

        self.equippable = equippable

        if self.equippable:
            self.equippable.parent = self
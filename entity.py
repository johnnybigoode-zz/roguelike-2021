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
        return self.parent.gamemap

    def spawn(self: T, gamemap: GameMap, x: int, y: int) -> T:
        """Spawn a copy of this instance at the given location"""
        clone = copy.deepcopy(self)
        clone.x = x
        clone.y = y
        clone.parent  = gamemap
        gamemap.entities.add(clone)
        return clone
    
    def place(self, x:int, y:int, gamemap: Optional[GameMap] = None) -> None:
        """place this entity at a new location handles moving across gamemaps"""
        self.x = x
        self.y = y
        if gamemap:
            if hasattr(self, "parent"): #possibily unitianilziaded
                self.parent.entities.remove(self)
            self.parent = gamemap
            gamemap.entities.add(self)

    def distance(self, x: int, y:int ) -> float:
        return math.sqrt((x - self.x) ** 2 + (y - self.y) ** 2)

    def move(self, dx: int, dy: int) -> None:
        # Move the entity by a given amount

        self.x += dx
        self.y += dy
        
class Actor(Entity):
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
        return bool(self.ai)

class Item(Entity):
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
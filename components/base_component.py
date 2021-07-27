"""
BaseComponent module which we will use to create our components.
These will always have a parent entity.
The default methods (properties) will give access to where the parent is spawned.
A component will be anything that needs to be attached to a parent entity.
Like making an item to be consumable or equipable. 
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from engine import Engine
    from entity import Entity
    from game_map import GameMap

class BaseComponent:
    """
    We import and inherit from BaseComponent, 
    which gives us access to the parent entity and the engine.
    """
    parent: Entity

    @property
    def gamemap(self) -> GameMap:
        """Returns gamemap parent entity exists in

        :return: Parent Entity's GameMap
        :rtype: GameMap
        """
        return self.parent.gamemap

    @property
    def engine(self) -> Engine:
        """Returns engine parent entity exists in

        :return: Parent Entity's Engine
        :rtype: Engine
        """
        return self.gamemap.engine
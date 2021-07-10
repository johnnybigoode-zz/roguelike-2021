from __future__ import annotations

from typing import Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from engine import Engine
    from entity import Entity

class Action:
    def __init__(self, entity: Entity) -> None:
        super().__init__()
        self.entity = entity

    @property
    def engine(self) -> Engine:
        """return the engine this actions belongs to"""
        return self.entity.gamemap.engine

    def perform(self) -> None:
        """Perform this action with the objects needed tio determine its scope.
        `self.engine` is the scope this action is being perfomed in
        `self.entity` is the object performing the action 
        
        This method must be overridden by Action subclasses.
        """
        raise NotImplementedError()

class EscapeAction(Action):
    def perform(self) -> None:
        raise SystemExit()

class ActionWithDirection(Action):
    def __init__(self, entity: Entity, dx: int, dy: int):
        super().__init__(entity)

        self.dx = dx
        self.dy = dy

    @property
    def dest_xy(self) -> Tuple[int, int]:
        """returns this actions destination"""
        return self.entity.x + self.dx, self.entity.y + self.dy

    @property
    def blocking_entity(self) -> Optional[Entity]:
        """return the blocking entity at this actions destination"""
        return self.engine.game_map.get_blocking_entity_at_location(*self.dest_xy)

    def perform(self) -> None:
        raise NotImplementedError()

class MeleeAction(ActionWithDirection):
    def perform(self) -> None:
        target = self.blocking_entity
        if not target:
            return #nothing to atackk
        
        print(f"You kick the {target.name}, much to its annoyance!")

class BumpAction(ActionWithDirection):
    def perform(self) -> None:
        if self.blocking_entity:
            return MeleeAction(self.entity, self.dx, self.dy).perform()
        else:
            return MovementAction(self.entity, self.dx, self.dy).perform()


class MovementAction(ActionWithDirection):
    def perform(self) -> None:
        dest_x, dest_y = self.dest_xy
        
        if not self.engine.game_map.in_bounds(dest_x, dest_y):
            return # destination is out of bounds.
        if (not self.engine.game_map.tiles["walkable"][dest_x, dest_y]):
            return # destination is blocked by a tile
        if (self.engine.game_map.get_blocking_entity_at_location(dest_x, dest_y)):
            return

        self.entity.move(self.dx, self.dy)
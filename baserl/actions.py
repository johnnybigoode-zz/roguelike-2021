"""
Actions are behaviors an Actor can perform
They are attached to Actor entities
"""

from __future__ import annotations

from typing import Optional, Tuple, TYPE_CHECKING

import color
import exceptions

if TYPE_CHECKING:
    from engine import Engine
    from entity import Actor, Entity, Item


class Action:
    """
    Defines the base class for all actions
    The 'perform' method must be implemented by all subclasses
    Are those subclasses? How does OOP work in Python?
    """

    def __init__(self, entity: Actor) -> None:
        """To init an Action, we need to know which Actor is performing it
        
        :param entity: The actor that will perform this action
        :type entity: Actor
        """
        super().__init__()
        self.entity = entity

    @property
    def engine(self) -> Engine:
        """Returns the Engine that this action is performed in.
        The engine is related to the gamemap that is referenced by the entity

        :return: The engine running the gamemap that the entity existis in
        :rtype: Engine
        """        
        return self.entity.gamemap.engine

    def perform(self) -> None:
        """Perform this action with the objects needed tio determine its scope.
        `self.engine` is the scope this action is being perfomed in
        `self.entity` is the object performing the action 

        This method must be overridden by Action subclasses.
        """
        raise NotImplementedError()


class PickupAction(Action):
    """Action when an entity will pick up an item from a tile

    :param Action: Since it's just the parent class, should we even comment it?
    :type Action: Action
    """
    def __init__(self, entity: Actor):
        """To init a PickupAction, we need to know which Actor is performing it

        :param entity: Who is performing it
        :type entity: Actor
        """
        super().__init__(entity)

    def perform(self) -> None:
        """The actual performance
        In this case, Actor will attempt to pick up an item from the tile
        This might raise exceptions.Impossible if there is nothing to pickup or if inventory is full
        """
        actor_location_x = self.entity.x
        actor_location_y = self.entity.y
        inventory = self.entity.inventory

        for item in self.engine.game_map.items:
            if(actor_location_x == item.x and actor_location_y == item.y):
                if (len(inventory.items) >= inventory.capacity):
                    raise exceptions.Impossible("Your inventory is full")

                self.engine.game_map.entities.remove(item)
                item.parent = self.entity.inventory
                inventory.items.append(item)

                self.engine.message_log.add_message(
                    f"You picked up the {item.name}!")
                return

        raise exceptions.Impossible("There is nothing to pick up.")


class ItemAction(Action):
    """Action related to using an Item

    :param Action: Again this is a subclass?
    :type Action: Action
    """
    def __init__(
        self, entity: Actor, item: Item, target_xy: Optional[Tuple[int, int]] = None
    ):
        """Initialization of item action

        :param entity: Actor who is using the item
        :type entity: Actor
        :param item: The item which is being used
        :type item: Item
        :param target_xy: If item is not self used (like a potion) passes the target of item use, defaults to None
        :type target_xy: Optional[Tuple[int, int]], optional
        """
        super().__init__(entity)
        self.item = item
        if not target_xy:
            target_xy = entity.x, entity.y
        self.target_xy = target_xy

    @property
    def target_actor(self) -> Optional[Actor]:
        """Return the actor at this actions destionation

        :return: The Actor at the destination - but what if its not an actor?
        :rtype: Optional[Actor]
        """
        return self.engine.game_map.get_actor_at_location(*self.target_xy)

    def perform(self) -> None:
        """
        Performs the action, the Item should know how it activates itself.
        """
        if self.item.consumable:
            self.item.consumable.activate(self)


class DropItem(Action):
    """Drop item from inventory

    :param Action: Parent class
    :type Action: Action
    """
    def perform(self) -> None:
        """
        Passes item to entity's inventory so it can be dropped
        """
        self.entity.inventory.drop(self.item)

class EquipAction(Action):
    """Equips equipabble item

    :param Action: Parent's class
    :type Action: Action
    """
    def __init__(self, entity: Actor, item: Item) -> None:
        """Constructor

        :param entity: Actor who will perform the action
        :type entity: Actor
        :param item: Item which will be equiped
        :type item: Item
        """
        super().__init__(entity)
        self.item = item

    def perform(self) -> None:
        """
        Passes item to entity's inventory so it can be equipped OR unequips 
        Basically toggle_equip eh?
        """
        self.entity.equipment.toggle_equip(self.item)

class WaitAction(Action):
    """Action that does nothing but passes a turn

    :param Action: Parent's class
    :type Action: Action
    """
    def perform(self) -> None:
        """
        Don't do anything, just pass the turn
        """
        pass

class TakeStairsAction(Action):
    """To make our character go down a set of stairs

    :param Action: Parent's class
    :type Action: Action
    """
    
    def perform(self) -> None:
        """Attemps to take the stairs, will raise exceptions.Impossible if there are no stairs
        """
        if (self.entity.x, self.entity.y) == self.engine.game_map.downstairs_location:
            self.engine.game_world.generate_floor()
            self.engine.message_log.add_message(
                f"You took the stairs down.")
        else:
            raise exceptions.Impossible("There are no stairs here.")

class ActionWithDirection(Action):
    """
    Sub class of Action that includes a direction
    Should be implemented by subclasses

    :param Action: Parent's class
    :type Action: Action
    """
    def __init__(self, entity: Actor, dx: int, dy: int):
        """Constructor

        :param entity: Actor who will perform the action
        :type entity: Actor
        :param dx: Action x direction
        :type dx: int
        :param dy: Action y direction
        :type dy: int
        """
        super().__init__(entity)

        self.dx = dx
        self.dy = dy

    @property
    def dest_xy(self) -> Tuple[int, int]:
        """
        Returns this actions destination
        It is the current entior's location plus the direction it is supposed to take

        :return: X,Y Coordinates of destination
        :rtype: Tuple[int, int]
        """
        
        return self.entity.x + self.dx, self.entity.y + self.dy

    @property
    def blocking_entity(self) -> Optional[Entity]:
        """
        Return the blocking entity at this actions destination

        :return: Blocking entity at destination
        :rtype: Optional[Entity]
        """
        return self.engine.game_map.get_blocking_entity_at_location(*self.dest_xy)

    @property
    def target_actor(self) -> Optional[Actor]:
        """
        Return the actor at this actions destination

        :return: The actor at destination
        :rtype: Optional[Actor]
        """
        return self.engine.game_map.get_actor_at_location(*self.dest_xy)

    def perform(self) -> None:
        """Method should be implemented by subclasses

        :raises NotImplementedError: [description]
        """
        raise NotImplementedError()


class MeleeAction(ActionWithDirection):
    """
    Attacks at direction

    :param ActionWithDirection: Parent's class
    :type ActionWithDirection: ActionWithDirection
    """
    def perform(self) -> None:
        """
        Attemps to attack Actor at direction

        :raises exceptions.Impossible: If no target to attack
        """
        target = self.target_actor
        if not target:
            raise exceptions.Impossible("Nothing to attack.")

        damage = self.entity.fighter.power - target.fighter.defense
        attack_desc = f"{self.entity.name.capitalize()} attacks {target.name}"
        if (self.entity is self.engine.player):
            attack_color = color.player_atk
        else:
            attack_color = color.enemy_atk

        if (damage > 0):

            self.engine.message_log.add_message(
                f"{attack_desc} for {damage} hit points.", attack_color
            )
            target.fighter.hp -= damage
        else:
            self.engine.message_log.add_message(
                f"{attack_desc} but does no damage.", attack_color
            )


class BumpAction(ActionWithDirection):
    """
    Bumps into an entity
    If entity is an actor, self.actor attemps to attack it
    If not, attemps to move actor.

    :param ActionWithDirection: Parent's class
    :type ActionWithDirection: ActionWithDirection
    """
    def perform(self) -> None:
        """
        If target is actor, returns a melee attack action that returns None
        Else, returns a move action that returns None

        :return: Implementation of ActionWithDirection
        :rtype: None
        """
        if self.target_actor:
            return MeleeAction(self.entity, self.dx, self.dy).perform()
        else:
            return MovementAction(self.entity, self.dx, self.dy).perform()


class MovementAction(ActionWithDirection):
    """Attemps to move actor to direction
    If destination is out of bounds, blocked by entity or non-walkable will :raises exceptions.Impossible:

    :param ActionWithDirection: Parent's Class
    :type ActionWithDirection: ActionWithDirection
    """
    def perform(self) -> None:
        """Checks if destition is reachable, if not :raises exceptions.Impossible:
        """
        dest_x, dest_y = self.dest_xy

        if not self.engine.game_map.in_bounds(dest_x, dest_y):
            raise exceptions.Impossible("The way is blocked")
        if (not self.engine.game_map.tiles["walkable"][dest_x, dest_y]):
            raise exceptions.Impossible("The way is blocked")
        if (self.engine.game_map.get_blocking_entity_at_location(dest_x, dest_y)):
            raise exceptions.Impossible("The way is blocked")

        self.entity.move(self.dx, self.dy)

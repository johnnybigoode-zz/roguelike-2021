"""
Class for consumable component
"""
from __future__ import annotations
from engine import Engine

from typing import Optional, TYPE_CHECKING

import actions
import color
import components.ai
import components.inventory
from components.base_component import BaseComponent
from exceptions import Impossible
from input_handlers import ActionOrHandler, AreaRangedAttackHandler, SingleRangedAttackHandler

if TYPE_CHECKING:
    from entity import Actor, Item


class Consumable(BaseComponent):
    """
    Mais class for consumable component
    """
    parent: Item

    def get_action(self, consumer: Actor) -> Optional[ActionOrHandler]:        
        """Return the action for behavior"""
        return actions.ItemAction(consumer, self.parent)

    def activate(self, action: actions.ItemAction) -> None:
        """
        Invoke this items ability
        `action` is the context for this activations
        Must be implemented by a consumable item
        """
        raise NotImplementedError

    def consume(self) -> None:
        """
        Invoes this items consume behavior
        Probably remove from iventory is its parent is inventory
        """
        entity = self.parent
        inventory = entity.parent
        if isinstance(inventory, components.inventory.Inventory):
            inventory.items.remove(entity)


class ConfusionConsumable(Consumable):
    """
    Class for causing confusion behavior
    """
    def __init__(self, number_of_turns: int):
        """Constructor

        :param number_of_turns: Number of turns which confusion will last
        :type number_of_turns: int
        """
        self.number_of_turns = number_of_turns

    def get_action(self, consumer: Actor) -> SingleRangedAttackHandler:
        """
        We will return a SingleRangeAttackHandler with the callback function for the effect

        :param consumer: Actor that will consume this item, might inflict its effects to another target
        :type consumer: Actor
        :return: 
        :rtype: SingleRangedAttackHandler
        """
        self.engine.message_log.add_message(
            "Select a target location.", color.needs_target
        )
        return SingleRangedAttackHandler(
            self.engine,
            callback = lambda xy: actions.ItemAction(consumer, self.parent, xy),
        )

    def activate(self, action: actions.ItemAction) -> None:
        """
        The actual behavior switch when we consume this consumable

        :param action: action context for this activation
        :type action: actions.ItemAction
        :raises Impossible: Can't cast outside of the field of view
        :raises Impossible: Target is not an enemy
        :raises Impossible: Cannot target yourself
        """

        consumer = action.entity
        target = action.target_actor

        if not self.engine.game_map.visible[action.target_xy]:
            raise Impossible("You cannot target an area you cannot see.")
        if not target:
            raise Impossible("You must select an enemy to target.")
        if target is consumer:
            raise Impossible("You cannot confuse yourself!")

        self.engine.message_log.add_message(
            f"The eyes of the {target.name} looks vacant, as it starts to stumble around!",
            color.status_effect_applied,
        )

        target.ai = components.ai.ConfusedEnemy(
            entity=target, previous_ai=target.ai, turns_remaining=self.number_of_turns,
        )
        self.consume()


class HealingConsumable(Consumable):
    """
    Class for healing consumable behavior
    """
    def __init__(self, amount: int):
        """
        Constructor
        
        :param amount: amount of HP the consumable will recover
        :type amount: int
        """
        self.amount = amount

    def activate(self, action: actions.ItemAction) -> None:
        """
        Activation of consumable

        :param action: Action context for this activation
        :type action: actions.ItemAction
        :raises Impossible: Can't heal if health is full
        """
        consumer = action.entity
        amount_recovered = consumer.fighter.heal(self.amount)

        if(amount_recovered > 0):
            self.engine.message_log.add_message(
                f"You consume the {self.parent.name}, and recover {amount_recovered} HP!",
                color.health_recovered,
            )
            self.consume()
        else:
            raise Impossible(f"Your health is already full.")


class LightingDamageConsumable(Consumable):
    """
    Class for lighting damage consumable behavior
    """
    def __init__(self, damage: int, maximun_range: int):
        """
        Constructor

        :param damage: Amount of damage that will be cause
        :type damage: int
        :param maximun_range: Maximum range of the attack
        :type maximun_range: int
        """
        self.damage = damage
        self.maximun_range = maximun_range

    def activate(self, action: actions.ItemAction) -> None:
        """
        Activation of lighting damage consumable
        Will find nearest enemy and damage it

        :param action: Action context for this activation
        :type action: actions.ItemAction
        :raises Impossible: Can't use if there's no close enemy
        """
        consumer = action.entity
        target = None
        closest_distance = self.maximun_range + 1.0

        for actor in self.engine.game_map.actors:
            if actor is not consumer and self.parent.gamemap.visible[actor.x, actor.y]:
                distance = consumer.distance(actor.x, actor.y)

                if (distance < closest_distance):
                    target = actor
                    closest_distance = distance

        if target:
            self.engine.message_log.add_message(
                f"A lighting bolt strikes the {target.name} with a loud thunder, for {self.damage} damage!"
            )
            target.fighter.take_damage(self.damage)
            self.consume()
        else:
            raise Impossible("No enemy is close enough to strike.")


class FireballDamageConsumable(Consumable):
    """
    Class for fireball damage consumable behavior
    """

    def __init__(self, damage: int, radius: int):
        """
        Constructor
        
        :param damage: Damaged caused by fireball
        :type damage: int
        :param radius: Radius of circle of effect of fireball
        :type radius: int
        """
        self.damage = damage
        self.radius = radius

    def get_action(self, consumer: Actor) -> AreaRangedAttackHandler:
        """Handles the area selection for spell

        :param consumer: Who will execute the spell
        :type consumer: Actor
        :return: 
        :rtype: AreaRangedAttackHandler
        """
        self.engine.message_log.add_message(
            "Select a target location.", color.needs_target
        )
        return AreaRangedAttackHandler(
            self.engine,
            radius=self.radius,
            callback=lambda xy: actions.ItemAction(consumer, self.parent, xy)
        )

    def activate(self, action: actions.ItemAction) -> None:
        """
        The damage to location 
        Will cause the same damage to all enemies in the circle defined by the radius

        :param action: Action context for this activation
        :type action: actions.ItemAction
        :raises Impossible: Cannot target area you cannot see
        :raises Impossible: Nothing to target
        """
        target_xy = action.target_xy

        if not self.engine.game_map.visible[target_xy]:
            raise Impossible("You cannot target an area you cannot see.")

        target_hit = False
        for actor in self.engine.game_map.actors:
            if actor.distance(*target_xy) <= self.radius:
                self.engine.message_log.add_message(
                    f"The {actor.name} is engulfed in a fiery explosion, taking {self.damage} damage!"
                )
                actor.fighter.take_damage(self.damage)
                target_hit = True

        if not target_hit:
            raise Impossible("There are no targets in the radius.")

        self.consume()

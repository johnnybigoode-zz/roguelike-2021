"""
Fighter module
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import color
from components.base_component import BaseComponent
from render_order import RenderOrder

if TYPE_CHECKING:
    from entity import Actor

class Fighter(BaseComponent):
    """
    Basically everything the player needs to interact with world
    """
    parent: Actor

    def __init__(self, hp: int, base_defense: int, base_power: int):
        """
        Constructor

        :param hp: Initial HP
        :type hp: int
        :param base_defense: Initial defense
        :type base_defense: int
        :param base_power: Initial power
        :type base_power: int
        """
        self.max_hp = hp
        self._hp = hp
        self.base_defense = base_defense
        self.base_power = base_power
        
    @property
    def hp(self) -> int:
        """
        Returns current hp
        """
        return self._hp

    @hp.setter
    def hp(self, value: int) -> None:
        """
        Sets current hp
        Will not go below 0 or max hp
        Will trigger self.die if hp is 0 and there is an AI component

        :param value: Value to be set
        :type value: int
        """
        self._hp = max(0, min(value, self.max_hp))
        if(self._hp == 0 and self.parent.ai):
            self.die()

    @property
    def defense(self) -> int:
        """
        Returns total defense, base + equipment bonus
        :return: Total defense
        :rtype: int
        """
        return self.base_defense + self.defense_bonus

    @property
    def power(self) -> int:
        """
        Returns total power, base + equipment bonus

        :return: Returns total power, base + equipment bonus
        :rtype: int
        """
        return self.base_power + self.power_bonus
    
    @property
    def defense_bonus(self) -> int:
        """
        Returns bonus defense provided by equipment
        """
        if self.parent.equipment:
            return self.parent.equipment.defense_bonus
        else:
            return 0

    @property
    def power_bonus(self) -> int:
        """
        Returns bonus power provided by equipment
        """
        if self.parent.equipment:
            return self.parent.equipment.power_bonus
        else:
            return 0


    def heal(self, amount: int):
        """
        Defines a heal function for the fighter

        :param amount: Amount to be realed
        :type amount: int
        :return: Amount recovered, if any
        :rtype: int
        """
        if (self.hp == self.max_hp):
            return 0

        new_hp_value = self.hp + amount

        if (new_hp_value > self.max_hp):
            new_hp_value = self.max_hp

        amount_recovered = new_hp_value - self.hp
        self.hp = new_hp_value

        return amount_recovered

    def take_damage(self, amount: int) -> None:
        """
        How this entity will take damage
        """
        self.hp -= amount
    
    def die(self) -> None:
        """
        Behavior when player dies. 
        """
        if(self.engine.player is self.parent):
            death_message = "You died!"
            death_message_color = color.player_die            
        else:
            death_message = f"{self.parent.name} is dead!"
            death_message_color = color.enemy_die

        self.parent.char = "%"
        self.parent.color = (191, 0, 0)
        self.parent.blocks_movement = False
        self.parent.ai = None
        self.parent.name = f"remains of {self.parent.name}"
        self.parent.render_order = RenderOrder.CORPSE

        self.engine.message_log.add_message(death_message, death_message_color)
        self.engine.player.level.add_xp(self.parent.level.xp_given)
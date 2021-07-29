"""
Module for level system
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from components.base_component import BaseComponent

if TYPE_CHECKING:
    from entity import Actor

class Level(BaseComponent):
    """
    Base class for level
    """
    parent: Actor

    def __init__(
        self, 
        current_level: int = 1,
        current_xp: int = 0,
        level_up_base: int = 0,
        level_up_factor: int = 150,
        xp_given: int = 0,
    ):
        """Constructor
        
        :param current_level: Current level, defaults to 1
        :type current_level: int, optional
        :param current_xp: Current amount of experience, defaults to 0
        :type current_xp: int, optional
        :param level_up_base: The base that should be taken in consideration when leveling up, defaults to 0
        :type level_up_base: int, optional
        :param level_up_factor: will be used as a factor vs the level up base to check next level xp requirements, defaults to 150
        :type level_up_factor: int, optional
        :param xp_given: Amount of xp that will be given if entity is killed, defaults to 0
        :type xp_given: int, optional
        """
        self.current_level = current_level
        self.current_xp = current_xp
        self.level_up_base = level_up_base
        self.level_up_factor = level_up_factor
        self.xp_given = xp_given

    @property
    def experience_to_next_level(self) -> int:
        """
        Returns the amount of experience needed to advance to the next level
        Which is the level_up_base + current_level * level_up_factor
        """
        return self.level_up_base + self.current_level * self.level_up_factor

    @property
    def requires_level_up(self) -> bool:
        """
        Bool that will be true if entity needs to level up
        """
        return self.current_xp > self.experience_to_next_level
    
    def add_xp(self, xp: int) -> None:
        """
        Add xp to itself
        """
        if xp == 0 or self.level_up_base == 0:
            return
        
        self.current_xp += xp
        self.engine.message_log.add_message(f'You gain {xp} experience points.')
        
        if self.requires_level_up:
            self.engine.message_log.add_message(
                 f"You advance to level {self.current_level + 1}!"
            )
            
    def increase_level(self) -> None:
        """Increase level by 1"""
        self.current_xp -= self.experience_to_next_level
        self.current_level += 1

    def increase_max_hp(self, amount: int) -> None:
        """
        Increase entity's max hp

        :param amount: Amount to increase max hp by
        :type amount: int
        """
        self.parent.fighter.max_hp += amount
        self.parent.fighter.hp += amount

        self.engine.message_log.add_message(f'Your health improves!')

        self.increase_level()

    def increase_power(self, amount: int = 1) -> None:
        """
        Increase entity's power

        :param amount: Amount of power to increase, defaults to 1
        :type amount: int, optional
        """
        self.parent.fighter.base_power += amount
        self.engine.message_log.add_message(f'Your feel stronger!')
        self.increase_level()

    def increase_defense(self, amount: int = 1) -> None:
        """
        Increase entity's defense

        :param amount: Amount of defense to increase, defaults to 1
        :type amount: int, optional
        """
        self.parent.fighter.base_defense += amount
        self.engine.message_log.add_message(f'Your defense improves!')
        self.increase_level()
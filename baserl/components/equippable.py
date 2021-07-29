"""
Equippable module
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from components.base_component import BaseComponent
from equipment_types import EquipmentType

if TYPE_CHECKING:
    from entity import Item

class Equippable(BaseComponent):
    """
    Main equippable class
    """
    parent: Item

    def __init__(
        self, 
        equipment_type: EquipmentType, 
        power_bonus: int = 0, 
        defense_bonus: int = 0
    ):
        """
        Constructor

        :param equipment_type: Defines what type of equipment this will be
        :type equipment_type: EquipmentType
        :param power_bonus: the power bonus this equipment will provide, defaults to 0
        :type power_bonus: int, optional
        :param defense_bonus: the defense bonus this will provide, defaults to 0
        :type defense_bonus: int, optional
        """

        self.equipment_type = equipment_type
        self.power_bonus = power_bonus
        self.defense_bonus = defense_bonus

class Dagger(Equippable):
    """
    Composition of weapond Dagger
    """
    def __init__(self):
        """
        Constructor, calls supper with the approrpiate arguments and bonus
        """
        super().__init__(
            equipment_type = EquipmentType.WEAPON,
            power_bonus = 2,
        )

class Sword(Equippable):
    """Composition of weapond Sword"""
    def __init__(self):
        """
        Constructor, calls supper with the approrpiate arguments and bonus
        """
        super().__init__(
            equipment_type = EquipmentType.WEAPON,
            power_bonus = 4,
        )

class LeatheArmor(Equippable):
    """Composition for Leather Armor"""
    def __init__(self):
        """
        Constructor, calls supper with the approrpiate arguments and bonus
        """
        super().__init__(
            equipment_type = EquipmentType.ARMOR,
            defense_bonus = 1,
        )

class ChainMail(Equippable):
    """Composition for Chain Mail"""
    def __init__(self):
        """
        Constructor, calls supper with the approrpiate arguments and bonus
        """
        super().__init__(
            equipment_type = EquipmentType.ARMOR,
            defense_bonus = 3,
        )
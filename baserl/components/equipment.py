"""
Module for equipment component
"""
from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from components.base_component import BaseComponent
from equipment_types import EquipmentType

if TYPE_CHECKING:
    from entity import Actor, Item

class Equipment(BaseComponent):
    """
    Main class for equipment
    """
    parent: Actor

    def __init__(
        self, 
        weapon: Optional[Item] = None,
        armor: Optional[Item] = None, 
    ):
        """
        Constructor

        :param weapon: Weapon equipment to start, defaults to None
        :type weapon: Optional[Item], optional
        :param armor: Armor equipment to start, defaults to None
        :type armor: Optional[Item], optional
        """
        self.weapon = weapon
        self.armor = armor

    @property
    def defense_bonus(self) -> int:
        """
        If armor, this houses the defense boost it provides

        :return: The defense bonus
        :rtype: int
        """
        bonus = 0

        if self.weapon is not None and self.weapon.equippable is not None:
            bonus += self.weapon.equippable.defense_bonus
        
        if self.armor is not None and self.armor.equippable is not None:
            bonus += self.armor.equippable.defense_bonus

        return bonus


    @property
    def power_bonus(self) -> int:
        """
        If weapon, this returns the power bonus

        :return: The power bonus
        :rtype: int
        """
        bonus = 0

        if self.weapon is not None and self.weapon.equippable is not None:
            bonus += self.weapon.equippable.power_bonus

        if self.armor is not None and self.armor.equippable is not None:
            bonus += self.armor.equippable.power_bonus

        return bonus

    def item_is_equippable(self, item: Item) -> bool:
        """
        Returns bool to check if Item has Equipment component
        """
        return self.weapon == item or self.armor == item

    def unequip_message(self, item_name: str) -> None:
        """
        Prints to message log when an item is unequipped
        """
        self.parent.gamemap.engine.message_log.add_message(
            f"You remove the {item_name}."
        )

    def equip_message(self, item_name: str) -> None:
        """
        Prints to log if an item is equipped
        """
        self.parent.gamemap.engine.message_log.add_message(
            f"You equip the {item_name}."
        )
        
    def equip_to_slot(self, slot: str, item: Item, add_message: bool) -> None:
        """
        Equips an item to a slot

        :param slot: Name of the slot
        :type slot: str
        :param item: Item to be equiped
        :type item: Item
        :param add_message: Bool to add message to message log
        :type add_message: bool
        """
        current_item = getattr(self, slot)

        if current_item is not None:
            self.unequip_from_slot(slot, add_message)

        setattr(self, slot, item)

        if add_message:
            self.equip_message(item.name)

    def unequip_from_slot(self, slot: str, add_message: bool) -> None:
        """
        Unequips an item from a slot

        :param slot: Name of the slot
        :type slot: str
        :param add_message: bool to add message to message log
        :type add_message: bool
        """
        current_item = getattr(self, slot)

        if add_message:
            self.unequip_from_slot(current_item.name)

        setattr(self, slot, None)

    def toggle_equip(self, equippable_item: Item, add_message: bool = True) -> None:
        """
        Equips or unequips an item

        :param equippable_item: The item to be toggled equip
        :type equippable_item: Item
        :param add_message: Message log for item equipment, defaults to True
        :type add_message: bool, optional
        """
        if (
            equippable_item.equippable and
            equippable_item.equippable.equipment_type == EquipmentType.WEAPON
        ):
            slot = "weapon"
        else:
            slot = "armor"

        if getattr(self, slot) == equippable_item:
            self.unequip_from_slot(slot, add_message)
        else:
            self.equip_to_slot(slot, equippable_item, add_message)
 
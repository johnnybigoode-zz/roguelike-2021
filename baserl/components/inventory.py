"""
Inventory component
"""
from __future__ import annotations

from typing import List, TYPE_CHECKING

from components.base_component import BaseComponent

if TYPE_CHECKING:
    from entity import Actor, Item

class Inventory(BaseComponent):
    """
    Iventory main class
    """
    parent: Actor

    def __init__(self, capacity: int):
        """
        Constructor 

        :param capacity: Amount of items the iventory will be able to hold
        :type capacity: int
        """
        self.capacity = capacity
        self.items: List[Item] = []

    def drop(self, item: Item) -> None:
        """
        Drop behavior, will remove items from self list

        :param item: Item to be dropped
        :type item: Item
        """
        self.items.remove(item)
        item.place(self.parent.x, self.parent.y, self.gamemap)

        self.engine.message_log.add_message(f"You dropped the {item.name}.")

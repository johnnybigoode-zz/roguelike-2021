"""
Enum class that represents the different equipment types. 
Currently, an equipment type is a type of weapon or armor.
More information on enum can be found at https://docs.python.org/3/library/enum.html
The 'auto' is a helper class (?) that will just give approviate values for Enum members
"""
from enum import auto, Enum

class EquipmentType(Enum):
    """
    Implementation of the class
    """
    WEAPON = auto()
    ARMOR = auto()
    
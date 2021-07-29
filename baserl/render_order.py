"""
Simple enum for render order
"""
from enum import auto, Enum

class RenderOrder(Enum):
    """
    Defines types for render order
    Which one comes first thou?
    """
    CORPSE = auto()
    ITEM = auto()
    ACTOR = auto()

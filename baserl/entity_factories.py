"""
Factory method pattern for creation of entities.
https://en.wikipedia.org/wiki/Factory_method_pattern
This is the part that can be abstracted into xml files, json files, etc.
Characters are from https://python-tcod.readthedocs.io/en/latest/tcod/charmap-reference.html#code-page-437
"""

from components.equippable import Equippable
from numpy import number
from components.ai import HostileEnemy
from components import consumable, equippable
from components.equipment import Equipment
from components.fighter import Fighter
from components.inventory import Inventory
from components.level import Level
from entity import Actor, Item
from tcod.tileset import CHARMAP_CP437

player = Actor(
    char=chr(0x2666),
    color=(255, 255, 255),
    name="Player",
    ai_cls=HostileEnemy,
    equipment=Equipment(),
    fighter=Fighter(hp=30, base_defense=2, base_power=5),
    inventory=Inventory(capacity=26),
    level=Level(level_up_base=200),
)

orc = Actor(
    char="o",
    color=(63, 127, 63),
    name="Orc",
    ai_cls=HostileEnemy,
    equipment=Equipment(),
    fighter=Fighter(hp=10, base_defense=0, base_power=3),
    inventory=Inventory(capacity=0),
    level=Level(xp_given=100),
)
troll = Actor(
    char="T",
    color=(0, 127, 0),
    name="Troll",
    ai_cls=HostileEnemy,
    equipment=Equipment(),
    fighter=Fighter(hp=16, base_defense=1, base_power=4),
    inventory=Inventory(capacity=0),
    level=Level(xp_given=35),
)

health_potion = Item(
    char="!",
    color=(127, 0, 255),
    name="Health Potion",
    consumable=consumable.HealingConsumable(amount=4),
)

lighting_scroll = Item(
    char="~",
    color=(255, 255, 0),
    name="Lighting Scroll",
    consumable=consumable.LightingDamageConsumable(damage=20, maximun_range=5),
)

confusion_scroll = Item(
    char="~",
    color=(207, 63, 255),
    name="Confusion Scroll",
    consumable=consumable.ConfusionConsumable(number_of_turns=10),
)

fireball_scroll = Item(
    char="~",
    color=(255, 0, 0),
    name="Fireball Scroll",
    consumable=consumable.FireballDamageConsumable(damage=12, radius=3),
)

dagger = Item( 
    char="/",
    color=(0, 191, 255),
    name="Dagger",
    equippable=equippable.Dagger()
)

sword = Item( 
    char="|",
    color=(0, 191, 255),
    name="Sword",
    equippable=equippable.Sword()
)

leather_armor = Item(
    char="[",
    color=(139, 69, 19),
    name="Leather Armor",
    equippable=equippable.LeatheArmor()
)

chain_mail = Item(
    char="]",
    color=(139, 69, 19),
    name="Chain Mail",
    equippable=equippable.ChainMail()
)


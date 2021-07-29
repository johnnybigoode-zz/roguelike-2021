"""
Module for render functions
"""

from __future__ import annotations

from typing import Tuple, TYPE_CHECKING

import color

if TYPE_CHECKING:
    from tcod import Console
    from engine import Engine
    from game_map import GameMap

def get_names_at_location(
    x: int, y: int, game_map: GameMap
) -> str:
    """
    Get names at location
    Search for entities at location

    :param x: x coordinate
    :type x: int
    :param y: y coordinate
    :type y: int
    :param game_map: game map to get names from
    :type game_map: GameMap
    :return: Entity names at location
    :rtype: str
    """
    if (not game_map.in_bounds(x, y) or not game_map.visible[x, y]):
        return ""

    names = ", ".join(
        entity.name 
        for entity in game_map.entities 
        if entity.x == x and entity.y == y
    )

    return names.capitalize()

def render_bar(
    console: Console, current_value: int, maximum_value: int, total_width: int
) -> None:
    """
    Function to render player's health bar

    :param console: Console to render to
    :type console: Console
    :param current_value: Current life value
    :type current_value: int
    :param maximum_value: Maximum life value
    :type maximum_value: int
    :param total_width: Total bar
    :type total_width: int
    """
    bar_width = int(float(current_value) / maximum_value * total_width)

    console.draw_rect(x=0, y=45, width=20, height=1, ch=1, bg=color.bar_empty)

    if (bar_width > 0):
        console.draw_rect(
            x=0, y=45, width=bar_width, height=1, ch=1, bg=color.bar_filled
        )

    console.print(
        x=1, y=45, string=f"HP: {current_value}/{maximum_value}", fg=color.bar_text
    )

def render_dungeon_level(
    console: Console, dungeon_level: int, location: Tuple[int, int]
):
    """
    Render the current floor/level of the dungeon

    :param console: Console to render to
    :type console: Console
    :param dungeon_level: What level of the dungeon is the player on
    :type dungeon_level: int
    :param location: Location to print dungeon level
    :type location: Tuple[int, int]
    """
    x, y = location
    console.print(x=x, y=y, string=f"Dungeon level: {dungeon_level}")

def render_names_at_mouse_location(
    console: Console, x: int, y: int, engine: Engine
) -> None:
    """
    Render name at mouse location
    Gets names at mouse location and prints on x, y

    :param console: Console to render to
    :type console: Console
    :param x: x coordinate
    :type x: int
    :param y: y coordinate
    :type y: int
    :param engine: Engine the mouse exists on
    :type engine: Engine
    """
    mouse_x, mouse_y = engine.mouse_location

    names_at_mouse_location = get_names_at_location(
        x=mouse_x, y=mouse_y, game_map=engine.game_map
    )

    console.print(x=x, y=y, string=names_at_mouse_location)

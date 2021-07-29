"""
This module will handle all the input from the user.
"""
from __future__ import annotations
from typing import Callable, Optional, Tuple, TYPE_CHECKING, Union

import os

import tcod
from tcod.event_constants import K_PAGEDOWN

import actions
from actions import (
    Action,
    BumpAction,
    PickupAction,
    WaitAction
)

import color
import exceptions

if TYPE_CHECKING:
    from engine import Engine
    from entity import Item


MOVE_KEYS = {
    # arrows keys
    tcod.event.K_UP: (0, -1),
    tcod.event.K_DOWN: (0, 1),
    tcod.event.K_LEFT: (-1, 0),
    tcod.event.K_RIGHT: (1, 0),
    tcod.event.K_HOME: (-1, -1),
    tcod.event.K_END: (-1, 1),
    tcod.event.K_PAGEUP: (1, -1),
    tcod.event.K_PAGEDOWN: (1, 1),
    # numpad keys
    tcod.event.K_KP_1: (-1, 1),
    tcod.event.K_KP_2: (0, 1),
    tcod.event.K_KP_3: (1, 1),
    tcod.event.K_KP_4: (-1, 0),
    tcod.event.K_KP_6: (1, 0),
    tcod.event.K_KP_7: (-1, -1),
    tcod.event.K_KP_8: (0, -1),
    tcod.event.K_KP_9: (1, -1),
    # vi keys
    tcod.event.K_h: (-1, 0),
    tcod.event.K_j: (0, 1),
    tcod.event.K_k: (0, -1),
    tcod.event.K_l: (1, 0),
    tcod.event.K_y: (-1, -1),
    tcod.event.K_u: (1, -1),
    tcod.event.K_b: (-1, 1),
    tcod.event.K_n: (1, 1),
}

WAIT_KEYS = {
    tcod.event.K_PERIOD,
    tcod.event.K_KP_5,
    tcod.event.K_CLEAR,
}

CONFIRM_KEYS = {
    tcod.event.K_RETURN,
    tcod.event.K_KP_ENTER,
}

ActionOrHandler = Union[Action, "BaseEventHandler"]

class BaseEventHandler(tcod.event.EventDispatch[ActionOrHandler]):
    """
    Base event handler that will be used to handle tcod's events
    tcod's event are a light-weight implementation of event handling built on calls to SDL
    https://python-tcod.readthedocs.io/en/latest/tcod/event.html

    :param tcod: An EventDispatch with a ActionOrHandler
    :type tcod: tcod.event.EventDispatch[ActionOrHandler]
    """
    def handle_events(self, event: tcod.event.Event) -> BaseEventHandler:
        """
        Handle an event and return the next active event handler
        
        :param event: Event to be handled
        :type event: tcod.event.Event
        :return: Next active event handler
        :rtype: BaseEventHandler
        """
        state = self.dispatch(event)
        if isinstance(state, BaseEventHandler):
            return state
        assert not isinstance(state, Action), f"{self!r} can not handle actions."
        return self

    def on_render(self, console: tcod.Console) -> None:
        """
        Should be implmemented by other events.

        :param console: Console to render on
        :type console: tcod.Console
        :raises NotImplementedError: Self descriptive no?
        """
        raise NotImplementedError()

    def ev_quit(self, event: tcod.event.Quit) -> Optional[Action]:
        """Quits the game"""
        raise SystemExit()

class PopupMessage(BaseEventHandler):
    """
    Display a popup text window.
    """

    def __init__(self, parent_handler: BaseEventHandler, text: str):
        """
        Constructor

        :param parent_handler: Parent event handler
        :type parent_handler: BaseEventHandler
        :param text: Text to render
        :type text: str
        """
        self.parent = parent_handler
        self.text = text

    def on_render(self, console: tcod.Console) -> None:
        """Render the parent and dim the result, then print the message on top.

        :param console: Console to be rendered on
        :type console: tcod.Console
        """
        self.parent.on_render(console)
        console.tiles_rgb["fg"] //= 8
        console.tiles_rgb["bg"] //= 8

        console.print(
            console.width // 2,
            console.height // 2,
            self.text,
            fg=color.white,
            bg=color.black,
            alignment=tcod.CENTER,
        )

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[BaseEventHandler]:
        """Any key returns to the parent handler."""
        return self.parent

class EventHandler(BaseEventHandler):
    """Will handle all events."""

    def __init__(self, engine: Engine):
        """Constructor

        :param engine: Which engine will use this handler
        :type engine: Engine
        """
        self.engine = engine

    def handle_events(self, event: tcod.event.Event) -> BaseEventHandler:
        """Handle the events

        :param event: Event to be handled
        :type event: tcod.event.Event
        :return: The event handler that should handle this event
        :rtype: BaseEventHandler
        """
        action_or_state = self.dispatch(event)
        if isinstance(action_or_state, BaseEventHandler):
            return action_or_state
        if self.handle_action(action_or_state):
            # A valid action was performed.
                if not self.engine.player.is_alive:
                # The player was killed sometime during or after the action.
                    return GameOverEventHandler(self.engine)
                elif self.engine.player.level.requires_level_up:
                    return LevelUpEventHandler(self.engine)
                return MainGameEventHandler(self.engine)  # Return to the main handler.
        return self

    def handle_action(self, action: Optional[Action]) -> bool:
        """
        Handles actions
        Returns true if advances a turn

        :param action: Action to be performed
        :type action: Optional[Action]
        :return: Bool for turn advance
        :rtype: bool
        """

        if (action is None):
            return False

        try:
            action.perform()
        except exceptions.Impossible as exc:
            self.engine.message_log.add_message(exc.args[0], color.impossible)
            return False  # skip enemy turn on exception

        self.engine.handle_enemy_turns()
        self.engine.update_fov()
        return True

    def ev_mousemotion(self, event: tcod.event.MouseMotion) -> None:
        """Handles mouse motion

        :param event: tcod specific MouseMotion event
        :type event: tcod.event.MouseMotion
        """
        if (self.engine.game_map.in_bounds(event.tile.x, event.tile.y)):
            self.engine.mouse_location = event.tile.x, event.tile.y

    def on_render(self, console: tcod.Console) -> Optional[Action]:
        """
        Render method 

        :param console: Console to be rendered on
        :type console: tcod.Console
        :return: No return tho
        :rtype: Optional[Action]
        """
        self.engine.render(console)


class MainGameEventHandler(EventHandler):
    """
    Handles the main game loop.

    :param EventHandler: Parent class
    :type EventHandler: EventHandler
    """
    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        """
        Key down event handler

        :param event: tcod event KeyDown to be handled
        :type event: tcod.event.KeyDown
        :raises SystemExit: In case user presses ESC to quit
        :return: If no action was performed, return Action. Otherwise return the appropriate handler
        :rtype: Optional[ActionOrHandler]
        """
        action: Optional[Action] = None

        key = event.sym
        modifier = event.mod
        player = self.engine.player

        if key == tcod.event.K_PERIOD and modifier & (
            tcod.event.KMOD_LSHIFT | tcod.event.KMOD_RSHIFT
        ):
            return actions.TakeStairsAction(player)

        if key in MOVE_KEYS:
            dx, dy = MOVE_KEYS[key]
            action = BumpAction(player, dx, dy)
        elif key in WAIT_KEYS:
            action = WaitAction(player, 0, 0)
        elif key == tcod.event.K_ESCAPE:
            raise SystemExit()
        elif key == tcod.event.K_v:
            return HistoryViewer(self.engine)
        elif key == tcod.event.K_g:
            action = PickupAction(player)
        elif key == tcod.event.K_i:
            return InventoryActivateHandler(self.engine)
        elif key == tcod.event.K_d:
            return InventoryDropHandler(self.engine)
        elif key == tcod.event.K_c:
            return CharacterScreenEventHandler(self.engine)
        elif key == tcod.event.K_SLASH:
            return LookHandler(self.engine)

        # No valid key was presset
        return action


class GameOverEventHandler(EventHandler):
    """
    Handles GameOver 

    :param EventHandler: Parent class
    :type EventHandler: EventHandler
    """
    def on_quit(self) -> None:
        """
        Handle exiting out of a finished game.
        If game not saved, avoids quitting without saving.

        :raises exceptions.QuitWithoutSaving:
        """
        if os.path.exists("savegame.sav"):
             os.remove("savegame.sav")  # Deletes the active save file.
        raise exceptions.QuitWithoutSaving()  # Avoid saving a finished game.

    def ev_quit(self, event: tcod.event.Quit) -> None:
        """Quits

        :param event: tcod event Quit to be handled
        :type event: tcod.event.Quit
        """
        self.on_quit()

    def ev_keydown(self, event: tcod.event.KeyDown) -> None:
        """Handles the ESC key to quit

        :param event: The event to quit
        :type event: tcod.event.KeyDown
        """
        if event.sym == tcod.event.K_ESCAPE:
            self.on_quit()


CURSOR_Y_KEYS = {
    tcod.event.K_UP: -1,
    tcod.event.K_DOWN: 1,
    tcod.event.K_PAGEUP: -10,
    tcod.event.K_PAGEDOWN: 10,
}


class HistoryViewer(EventHandler):
    """
    Class to print history on a larger window that can be navigated

    :param EventHandler: Parent's class
    :type EventHandler: [type]
    """

    def __init__(self, engine: Engine):
        """Constructor

        :param engine: Engine to render the history
        :type engine: Engine
        """
        super().__init__(engine)
        self.log_length = len(engine.message_log.messages)
        self.cursor = self.log_length - 1

    def on_render(self, console: tcod.Console) -> None:
        """
        Renders the history viewer

        :param console: Console to render on
        :type console: tcod.Console
        """
        super().on_render(console)  # draw mainstate

        log_console = tcod.Console(console.width - 6, console.height - 6)

        # draw a frame with custom banner title
        log_console.draw_frame(0, 0, log_console.width, log_console.height)
        log_console.print_box(
            0, 0, log_console.width, 1, "┤Message history├", alignment=tcod.CENTER
        )

        # render the message log using the cursor parameter
        self.engine.message_log.render_messages(
            log_console,
            1,
            1,
            log_console.width - 2,
            log_console.height - 2,
            self.engine.message_log.messages[: self.cursor + 1],
        )
        log_console.blit(console, 3, 3)

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[MainGameEventHandler]:
        """
        Special ev_keydown handler for the history viewer

        :param event: if key down when History Viewer is active, handle the key
        :type event: tcod.event.KeyDown
        :return: Returns main event handler if any non key for viewer is pressed or none
        :rtype: Optional[MainGameEventHandler]
        """
        # fancy conditional movement to make it feel right
        if (event.sym in CURSOR_Y_KEYS):
            adjust = CURSOR_Y_KEYS[event.sym]
            if (adjust < 0 and self.cursor == 0):
                # only move from top to bottom when ur on the edge
                self.cursor = self.log_length - 1
            elif (adjust > 0 and self.cursor == self.log_length - 1):
                # same with bottom movement
                self.cursor = 0
            else:
                # otherwise move while staying clamped to the bounds of the history log
                self.cursor = max(
                    0, min(self.cursor + adjust, self.log_length - 1))
        elif (event.sym == tcod.event.K_HOME):
            self.cursor = 0  # move to top message
        elif (event.sym == tcod.event.K_END):
            self.cursor = self.log_length - 1  # move direct to last message
        else:  # any other key moves back to main state
            return MainGameEventHandler(self.engine)

        return None


class AskUserEventHandler(EventHandler):
    """
    Handles special user input, like inventory
    Shouldn't History Viewer be a child of this?

    :param EventHandler: Parent Class
    :type EventHandler: EventHandler
    """

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        """
        By default any key exits this input handler

        :param event: Key down event
        :type event: tcod.event.KeyDown
        :return: Returns none or self.on_exit, which is MainEventHandler
        :rtype: Optional[ActionOrHandler]
        """
        if event.sym in {  # Ignore modifier keys.
            tcod.event.K_LSHIFT,
            tcod.event.K_RSHIFT,
            tcod.event.K_LCTRL,
            tcod.event.K_RCTRL,
            tcod.event.K_LALT,
            tcod.event.K_RALT,
        }:
            return None
        return self.on_exit()

    def ev_mousebuttondown(
          self, event: tcod.event.MouseButtonDown
     ) -> Optional[ActionOrHandler]:
        """
        By default, mouse click will exit this handler

        :param event: Mouse button down event
        :type event: tcod.event.MouseButtonDown
        :return: Returns self.on_exit, which is MainEventHandler
        :rtype: Optional[ActionOrHandler]
        """
        return self.on_exit()

    def on_exit(self) -> Optional[ActionOrHandler]:
        """
        Just returns the maingame event handler

        :return: MainGameEventHandler
        :rtype: Optional[ActionOrHandler]
        """
        return MainGameEventHandler(self.engine)

class CharacterScreenEventHandler(AskUserEventHandler):
    """
    Class for Character information screen
    """
    TITLE = "Character Information"

    def on_render(self, console: tcod.Console) -> None:
        """
        Char Screen render, 
        Will render parent, before rendering over. 
        
        :param console: Console to be printed on
        :type console: tcod.Console
        """
        super().on_render(console)

        if self.engine.player.x <= 30:
            x = 40
        else:
            x = 0

        y = 0

        width = len(self.TITLE) + 4

        console.draw_frame(
            x=x,
            y=y,
            width=width,
            height=7,
            title=self.TITLE,
            clear=True,
            fg=(255, 255, 255),
            bg=(0, 0, 0),            
        )

        console.print(
            x=x + 1, y=y + 1, string=f"Level: {self.engine.player.level.current_level}"
        )
        console.print(
            x=x + 1, y=y + 2, string=f"XP: {self.engine.player.level.current_xp}"
        )
        console.print(
            x=x + 1,
            y=y + 3,
            string=f"XP for next Level: {self.engine.player.level.experience_to_next_level}",
        )

        console.print(
            x=x + 1, y=y + 4, string=f"Attack: {self.engine.player.fighter.power}"
        )
        console.print(
            x=x + 1, y=y + 5, string=f"Defense: {self.engine.player.fighter.defense}"
        )

class LevelUpEventHandler(AskUserEventHandler):
    """
    Handler for Level Up event

    :param AskUserEventHandler: Parent Class
    :type AskUserEventHandler: AskUserEventHandler
    """
    TITLE = "Level Up!"

    def on_render(self, console: tcod.Console) -> None:
        """
        Render parent then renders over

        :param console: Console to render on
        :type console: tcod.Console
        """
        super().on_render(console)

        if self.engine.player.x <= 30:
            x = 40
        else:
            x = 0

        console.draw_frame(
            x=x,
            y=0,
            width=35,
            height=8,
            title=self.TITLE,
            clear=True,
            fg=(255, 255, 255),
            bg=(0, 0, 0),
        )

        console.print(x=x + 1, y=1, string="Congratulations! You level up!")
        console.print(x=x + 1, y=2, string="Select an attribute to increase:")

        console.print(
            x=x + 1,
            y=4,
            string=f"A.) Constitution (+20 HP, from {self.engine.player.fighter.max_hp})",
        )

        console.print(
            x=x + 1,
            y=5,
            string=f"B.) Strenght (+1 Attack, from {self.engine.player.fighter.power})",
        )

        console.print(
            x=x + 1,
            y=6,
            string=f"C.) Agility (+1 Defense, from {self.engine.player.fighter.defense})",
        )

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        """
        Level up key down event handler.
        Will accept keys related to options presented to player
        If invalid, just adds a log message and stays on the same screen

        :param event: Key down event
        :type event: tcod.event.KeyDown
        :return: Should return super().ev_keydown(event) eventually
        :rtype: Optional[ActionOrHandler]
        """
        player = self.engine.player
        key = event.sym
        index = key - tcod.event.K_a

        if 0 <= index <= 2:
            if index == 0:
                player.level.increase_max_hp(20)
            if index == 1:
                player.level.increase_power()
            if index == 2:
                player.level.increase_defense()
        else:
            self.engine.message_log.add_message("Invalid entry", color.invalid)

            return None

        return super().ev_keydown(event)

    def ev_mousebuttondown(self, event: tcod.event.MouseButtonDown) -> Optional[ActionOrHandler]:
        """
        Does nothing if mouse button is pressed. 
        Default behavior would exit the current handler
        """
        return None


class InventoryEventHandler(AskUserEventHandler):
    """
    Class to handle user inventory

    :param AskUserEventHandler: Parent Class
    :type AskUserEventHandler: AskUserEventHandler
    """
    TITLE = "<missing title>"

    def on_render(self, console: tcod.Console) -> None:
        """
        Renders super then renders over it

        :param console: Console to render on
        :type console: tcod.Console
        """
        super().on_render(console)
        number_of_items_in_inventory = len(self.engine.player.inventory.items)

        height = number_of_items_in_inventory + 2

        if height <= 3:
            height = 3

        if self.engine.player.x <= 30:
            x = 40
        else:
            x = 0

        y = 0

        width = len(self.TITLE) + 4

        console.draw_frame(
            x=x,
            y=y,
            width=width,
            height=height,
            title=self.TITLE,
            clear=True,
            fg=(255, 255, 255),
            bg=(0, 0, 0,)
        )

        if number_of_items_in_inventory > 0:
            for i, item in enumerate(self.engine.player.inventory.items):
                item_key = chr(ord("a") + i)
                is_equipped = self.engine.player.equipment.item_is_equippable(item)
                item_string = f"({item_key}) {item.name}"
                if is_equipped:
                    item_string = f"{item_string} (E)"
                console.print(x + 1, y + i + 1, item_string)
        else:
            console.print(x + 1, y + 1, "(Empty)")

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        """
        Key down handler for inventory
        Takes any key from keyboard to pick from iventory

        :param event: Key down event
        :type event: tcod.event.KeyDown
        :return: Eventually returns super ev keydown 
        :rtype: Optional[ActionOrHandler]
        """
        player = self.engine.player
        key = event.sym
        index = key - tcod.event.K_a

        if (0 <= index <= 26):
            try:
                selected_item = player.inventory.items[index]
            except IndexError:
                self.engine.message_log.add_message(
                    "Invalid entry.", color.invalid)
                return None
            return self.on_item_selected(selected_item)
        return super().ev_keydown(event)

    def on_item_selected(self, item: Item) -> Optional[ActionOrHandler]:
        """
        Should be implemented by child class
        """
        raise NotImplementedError()


class InventoryActivateHandler(InventoryEventHandler):
    """
    Class to handle inventory activation

    :param InventoryEventHandler: Parent Class
    :type InventoryEventHandler: IventoryEventHandler
    """
    TITLE = "Select item to use"

    def on_item_selected(self, item: Item) -> Optional[Action]:
        """[summary]

        :param item: Selected Item
        :type item: Item
        :return: Returns action to be performed or None if no component found
        :rtype: Optional[Action]
        """
        if item.consumable:
            # Return the action for the selected item.
            return item.consumable.get_action(self.engine.player)
        elif item.equippable:
            return actions.EquipAction(self.engine.player, item)
        else:
            return None


class InventoryDropHandler(InventoryEventHandler):
    """
    Handles dropping item from iventory

    :param InventoryEventHandler: Parent Class
    :type InventoryEventHandler: IventoryEventHandler
    """
    TITLE = "Select item to drop"

    def on_item_selected(self, item: Item) -> Optional[ActionOrHandler]:
        """
        Handles dropping item from inventory

        :param item: Item to be dropped
        :type item: Item
        :return: actions.DropItem()
        :rtype: Optional[ActionOrHandler]
        """
        return actions.DropItem(self.engine.player, item)


class SelectIndexHandler(AskUserEventHandler):
    """
    Handler when you need to select a coordinate on the map

    :param AskUserEventHandler: Parent Class
    :type AskUserEventHandler: AskUserEventHandler
    """
    def __init__(self, engine: Engine):
        """
        Constructor

        :param engine: Engine which player is in
        :type engine: Engine
        """
        super().__init__(engine)
        player = self.engine.player
        engine.mouse_location = player.x, player.y

    def on_render(self, console: tcod.Console) -> None:
        """
        Render super then 
        Will take mouse information and render over

        :param console: Console to render on
        :type console: tcod.Console
        """
        super().on_render(console)
        x, y = self.engine.mouse_location
        console.tiles_rgb["bg"][x, y] = color.white
        console.tiles_rgb["fg"][x, y] = color.black

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        """
        Key down event handler for Select index handler

        :param event: Key down event
        :type event: tcod.event.KeyDown
        :return: super().ev_keydown
        :rtype: Optional[ActionOrHandler]
        """
        key = event.sym
        if (key in MOVE_KEYS):
            modifier = 1
            if event.mod & (tcod.event.KMOD_LSHIFT | tcod.event.KMOD_RSHIFT):
                modifier *= 5
            if event.mod & (tcod.event.KMOD_LCTRL | tcod.event.KMOD_RCTRL):
                modifier *= 10
            if event.mod & (tcod.event.KMOD_LALT | tcod.event.KMOD_RALT):
                modifier *= 20

            x, y = self.engine.mouse_location
            dx, dy = MOVE_KEYS[key]
            x += dx * modifier
            y += dy * modifier
            # clamp cursos index to map size
            x = max(0, min(x, self.engine.game_map.width - 1))
            y = max(0, min(y, self.engine.game_map.height - 1))
            self.engine.mouse_location = x, y
            return None
        elif key in CONFIRM_KEYS:
            return self.on_index_selected(*self.engine.mouse_location)

        return super().ev_keydown(event)

    def ev_mousebuttondown(self, event: tcod.event.MouseButtonDown) -> Optional[ActionOrHandler]:
        """
        Handles mouse click when selecting index

        :param event: The Mouse Click event
        :type event: tcod.event.MouseButtonDown
        :return: returns super with mousebutton or on_index_selected
        :rtype: Optional[ActionOrHandler]
        """
        if self.engine.game_map.in_bounds(*event.tile):
            if event.button == 1:
                return self.on_index_selected(*event.tile)

        return super().ev_mousebuttondown(event)

    def on_index_selected(self, x: int, y: int) -> Optional[ActionOrHandler]:
        """
        This method is called when the user selects an index
        It should be implemented in the child class

        :param x: x coordinate of selected index
        :type x: int
        :param y: y coordinate selected index
        :type y: int
        :raises NotImplementedError: Somebody forgot to implement this
        :return: Might return an action or a handler
        :rtype: Optional[ActionOrHandler]
        """
        raise NotImplementedError()


class LookHandler(SelectIndexHandler):
    """
    Will simply return the game to MainGameEventHandler

    :param SelectIndexHandler: Parent Class
    :type SelectIndexHandler: SelectIndexHandler
    """
    def on_index_selected(self, x: int, y: int) -> MainGameEventHandler:
        """Returns to main, passes no information
        """
        return MainGameEventHandler(self.engine)


class SingleRangedAttackHandler(SelectIndexHandler):
    """
    Handles ranged single target attack

    """
    def __init__(
        self, engine: Engine, callback: Callable[[Tuple[int, int]], Optional[Action]]
    ):
        """
        Constructor

        :param engine: Engine the player is in
        :type engine: Engine
        :param callback: Function to call when location has been picked
        :type callback: Callable[[Tuple[int, int]], Optional[Action]]
        """
        super().__init__(engine)
        self.callback = callback

    def on_index_selected(self, x: int, y: int) -> Optional[Action]:
        """
        When index is selected, passes information to call back function

        :param x: x coordinate of selected
        :type x: int
        :param y: y coordinate of selected
        :type y: int
        :return: returns an optional action
        :rtype: Optional[Action]
        """
        return self.callback((x, y))


class AreaRangedAttackHandler(SelectIndexHandler):
    """
    Handles an area target attack
    """
    def __init__(
        self,
        engine: Engine,
        radius: int,
        callback: Callable[[Tuple[int, int]], Optional[Action]],
    ):
        """
        Constructor

        :param engine: Engine player is in
        :type engine: Engine
        :param radius: Radius of area to target
        :type radius: int
        :param callback: Function to call when location has been picked
        :type callback: Callable[[Tuple[int, int]], Optional[Action]]
        """
        super().__init__(engine)
        self.radius = radius
        self.callback = callback

    def on_render(self, console: tcod.Console) -> None:
        """
        Renders affected area over super.on_render
        """
        super().on_render(console)

        x, y = self.engine.mouse_location

        # show affected area
        console.draw_frame(
            x=x - self.radius - 1,
            y=y - self.radius - 1,
            width=self.radius ** 2,
            height=self.radius ** 2,
            fg=color.red,
            clear=False,
        )

    def on_index_selected(self, x: int, y: int) -> Optional[Action]:
        """
        Calls back function with selected coordinate

        :param x: x coordinate
        :type x: int
        :param y: y coordinate
        :type y: int
        :return: ?
        :rtype: Optional[Action]
        """
        return self.callback((x, y))

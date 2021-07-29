"""
AI Module
"""
from __future__ import annotations

import random
from typing import List, Optional, Tuple, TYPE_CHECKING

import numpy as np # type: ignore
import tcod

from actions import Action, BumpAction, MeleeAction, MovementAction, WaitAction

if TYPE_CHECKING:
    from entity import Actor

class BaseAI(Action):
    """Base AI for all entities that would need an AI
    At the start of the tutorial it was a BaseComponent subclass too
    http://rogueliketutorials.com/tutorials/tcod/v2/part-8/

    :param Action: The BaseAI Needs to be a subclass of Action because it needs behavior?
    :type Action: Action
    """
    entity: Actor

    def perform(self) -> None:
        """
        What this Actor should do when it is enemy turn
        Needs to implement or else
        :raises NotImplementedError:
        """
        raise NotImplementedError()

    def get_path_to(self, dest_x: int, dest_y: int) -> List[Tuple[int, int]]:
        """
        Compute and return a path to target position
        If there is no valid path, returns an empty list
        """

        #copy the walkable array
        cost = np.array(self.entity.gamemap.tiles["walkable"], dtype=np.int8)

        for entity in self.entity.gamemap.entities:
            #chec that an entity blocks movement and the cost isnt zero (blocking)
            if entity.blocks_movement and cost[entity.x, entity.y]:
                #add to cost of blocked position
                #lower number means more enemies will crowd behind eachother
                #higher number means enemies will take longer paths to surround player
                cost[entity.x, entity.y] += 10
            
        #create a graph from the cost array and pass that to pathfinder
        graph = tcod.path.SimpleGraph(cost=cost, cardinal=2, diagonal=3)
        pathfinder = tcod.path.Pathfinder(graph)

        pathfinder.add_root((self.entity.x, self.entity.y)) #start pos

        #compute the path to the destination and remove starting point
        path: List[List[int]] = pathfinder.path_to((dest_x, dest_y))[1:].tolist()

        #CONVERT FROM LIST TO LIST TUPLE
        return [(index[0], index[1]) for index in path]

class HostileEnemy(BaseAI):
    """
    Implementation of BaseAI
    """

    def __init__(self, entity: Actor):
        """Constructor

        :param entity: The entity, but actually Actor that this behavior is attached to
        :type entity: Actor
        """
        super().__init__(entity)        
        self.path: List[Tuple[int, int]] =[]

    def perform(self) -> None:
        """
        Searchs for the player and moves towards their position
        """
        target = self.engine.player
        dx = target.x - self.entity.x
        dy = target.y - self.entity.y
        distance = max(abs(dx), abs(dy)) #Chebyshev distance

        if self.engine.game_map.visible[self.entity.x, self.entity.y]:
            if (distance <= 1):
                return MeleeAction(self.entity, dx, dy).perform()

            self.path = self.get_path_to(target.x, target.y)
        
        if self.path:
            dest_x, dest_y = self.path.pop(0)
            return MovementAction(
                self.entity, dest_x - self.entity.x, dest_y - self.entity.y,
            ).perform()

        return WaitAction(self.entity).perform()

class ConfusedEnemy(BaseAI):
    """
    Behavior when a AI is confused
    """
    def __init__(
        self, entity: Actor, previous_ai: Optional[BaseAI], turns_remaining: int
    ):
        """
        Constructor

        :param entity: Actor which is confused
        :type entity: Actor
        :param previous_ai: Previous AI of the entity
        :type previous_ai: Optional[BaseAI]
        :param turns_remaining: Turns remaining before the AI is no longer confused and resumes previous AI
        :type turns_remaining: int
        """
        super().__init__(entity)

        self.previous_ai = previous_ai
        self.turns_remaining = turns_remaining

    def perform(self) -> None:
        """
        If player is confused, take a random walk towards any tile around
        """
        if self.turns_remaining <= 0:
            self.engine.message_log.add_message(
                f"The {self.entity.name} is no longer confused."
            )
            self.entity.ai = self.previous_ai
        else:
            direction_x, direction_y = random.choice(
                [
                    (-1, -1), #nw
                    (0, -1), #n
                    (1, -1), #ne
                    
                    (-1, 0), #w
                    (1, 0), #e

                    (-1, 1), #sw
                    (0, 1), #s
                    (1, 1), #se
                ]
            )

            self.turns_remaining -= 1

            return BumpAction(self.entity, direction_x, direction_y,).perform()
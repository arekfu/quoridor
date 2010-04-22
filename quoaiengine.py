#!/usr/bin/env python

from quoboard import up, right, down, left, vdir, logging

class QuoAIEngine:
    """AI engine."""

    def __init__(self, h, goal):
        self.h == h

    def get_move(self, board):
        """Given a board, choose the next move."""

        self.update_others(board)
        self.update_enemy(board)
        self.think(board)

    def update_others(self, board):
        self.others = filter(lambda q: q.h != self.h, board.pp)
        self.me = filter(lambda q: q.h == self.h, board.pp)[0]
        if len(self.others) + 1 != board.nplayers:
            logging.critical("len(others) + 1 != nplayers")
            raise

    def update_enemy(self, board):
        """Determine the "enemy", i.e. the pawn closest to the goal."""
        self.enemy = self.others[0]
        closest = board.distance_to_goal(self.others[0].position, self.others[0].goal)
        for p in self.others[1:]:
            distance = board.distance_to_goal(p.position, p.goal)
            if distance < closest:
                closest = distance
                self.enemy = p

    def think(self):
        pass

    def evaluate_position_others(self, board):
        """Merit function for the evaluation of a position.
        
        Takes into account all the opponents."""
        return float(board.distance_to_goal(self.me.position, self.me.goal)) /
            float(min( [ board.distance_to_goal(p.position, p.goal) for p in self.others ] ))

    def evaluate_position_enemy(self, board):
        """Merit function for the evaluation of a position.
        
        Takes into account only the "enemy" pawn."""
        return float(board.distance_to_goal(self.me.position, self.me.goal)) /
            float(board.distance_to_goal(self.enemy.position, self.enemy.goal))


#!/usr/bin/env python

from quoboard import up, right, down, left, vdir, logging
import quoboard
import copy, random
from collections import deque

class QuoAIEngine:
    """AI engine."""

    def __init__(self, h):
        self.h = h

    def get_move(self, board):
        """Given a board, choose the next move."""

        self.board = board
        self.identify_me_and_others()
        self.identify_enemy()
        return self.choose_move()

    def identify_me_and_others(self):
        """Identify our and other players' Pawns."""
        
        self.me = filter(lambda q: q.h == self.h, self.board.pp)[0]
        self.others = self.board.pp[self.board.pp.index(self.me)+1:] + self.board.pp[:self.board.pp.index(self.me)]
        if len(self.others) + 1 != self.board.nplayers:
            logging.critical("len(others) == %d, nplayers == %d", len(self.others), self.board.nplayers)
            raise

    def identify_enemy(self):
        """Determine the "enemy", i.e. the pawn closest to the goal."""
        
        for p in self.others:
            p.distance = self.board.distance_to_goal(p)
        closest = min( p.distance for p in self.others )
        self.enemy = random.choice(filter(lambda p: p.distance==closest, self.others))

    def choose_move(self):
        """Think about how to move.

        Uses a minimax strategy."""

        logging.debug('Choosing a new move')
        ms_me = self.possible_moves(self.me)
        self.running_min = 9999999
        for m_me in ms_me:
            self.max_loss = 0
            logging.debug('Considering m_me == %s', m_me.s)
            if self.board.apply_move(self.h, m_me):
                logging.debug('Accepted')
                if self.board.check_win(self.h):
                    return m_me
                others_queue = deque(self.others)
                self.move_others(others_queue)
                self.board.restore_move(self.h, m_me)
                logging.debug('self.max_loss is now %d', self.max_loss)
                m_me.max_loss = self.max_loss
                logging.debug('m_me.max_loss is now %d', m_me.max_loss)
                self.running_min = min(self.running_min, m_me.max_loss)
                logging.debug('self.running_min is now %d', self.running_min)
        del self.max_loss
        
        m = min(filter(lambda m: hasattr(m,'max_loss'), ms_me), key=lambda m: m.max_loss)
        logging.debug('move chosen: %s', m.s)
        return min(filter(lambda m: hasattr(m,'max_loss'), ms_me), key=lambda m: m.max_loss)

    def move_others(self, queue):
        """Recursively move the other Pawns."""

        if queue:
            p = queue.popleft()
            for m_p in self.possible_moves(p):
                logging.debug('Considering m_p == %s', m_p.s)
                if self.board.apply_move(p.h, m_p):
                    logging.debug('Accepted')
                    self.move_others(queue)
                    logging.debug('self.max_loss is now %d', self.max_loss)
                    self.board.restore_move(p.h, m_p)
                    logging.debug('int(self.max_loss+0.5), int(self.running_min+0.5), int(self.max_loss+0.5) > int(self.running_min+0.5): %d, %d, %s', int(self.max_loss+0.5), int(self.running_min+0.5), repr(int(self.max_loss+0.5) > int(self.running_min+0.5)))
                    if int(self.max_loss+0.5) > int(self.running_min+0.5):
                        logging.debug('Breaking out, max_loss == %d > running_min == %d', self.max_loss, self.running_min)
                        queue=[]
                        break
        else:
            self.max_loss = max(self.max_loss, self.evaluate_position_enemy())
            # Or, alternatively:
            # self.max_loss = max(self.max_loss, self.evaluate_position_others())

    class Move:
        """Move class.

        Moves are encoded as strings. An initial "m" character indicates a
        move, and should be followed by one of the directions (1, 2, 4, 8). An
        initial "b" character indicates a barrier, and should be followed by
        two digits (the coordinates of the barrier origin) and a direction."""

        def __init__(self, s):
            self.s = s

    def possible_moves(self, p):
        """Return all the possible moves for pawn p."""

        # Look for moves
        moves = [ self.Move("m " + str(d)) for d in self.sort_best_moves(p)
            if self.board.moves[p.position[0]][p.position[1]] & d ]

        # Look for barriers
        for x in range(self.board.side):
            for y in range(self.board.side):
                for d in [up, right, down, left]:
                    if self.board.check_barrier(quoboard.Barrier(x, y, d)):
                        moves.append( self.Move("b " + str(x) + " " + str(y) + " " + str(d)) )

        return moves

    def sort_best_moves(self, p):
        """Returns the best possible moves, sorted by path length."""

        dist = self.board.dists[self.board.pp.index(p)]

        return sorted([ d for d in [up, right, down, left] if self.board.moves[p.position[0]][p.position[1]] & d and dist[p.position[0]][p.position[1]] >= 0],
            key = lambda d: dist[p.position[0]+vdir[d][0]][p.position[1]+vdir[d][1]] )

    def evaluate_position_others(self):
        """Merit function for the evaluation of a position.
        
        Takes into account all the opponents. Large == bad."""
        return float(self.board.distance_to_goal(self.me) / \
            float(min( self.board.distance_to_goal(p) for p in self.others )+1))

    def evaluate_position_enemy(self):
        """Merit function for the evaluation of a position.
        
        Takes into account only the "enemy" pawn. Large == bad."""
        #return float(self.board.distance_to_goal(self.me.position, self.me.goal)) / \
        #    float(self.board.distance_to_goal(self.enemy.position, self.enemy.goal)+1)
        return self.board.distance_to_goal(self.me) - \
            self.board.distance_to_goal(self.enemy)+1


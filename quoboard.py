#!/usr/bin/env python

# For debugging!
import pdb

# Set up logging
import logging, os.path
logging.basicConfig(level=logging.DEBUG,
        format='%(asctime)s %(levelname)-8s %(message)s',
        datefmt='%a, %d %b %Y %H:%M:%S',
        filename=os.path.expanduser('~/.quoserver.log'))

from collections import deque

# Global variables
global up, right, down, left
global vdir

up=1
right=2
down=4
left=8
enqueued = 1
visited = 2
visited_or_enqueued = visited | enqueued
mask = ~visited_or_enqueued
vdir={
                up:     (0,-1),
                right:  (1,0),
                down:   (0,1),
                left:   (-1,0)
            }
length = 2



# Class definitions

class Barrier:
    """Barrier class"""
    # Barrier positions are defined as being (0,0) in the top-left corner
    # of the board. Thus each coordinate ranges from 0 to side
    def __init__(self,x,y,direction,length=2):
        if direction!=up and direction!=right and direction!=down and direction!=left:
            logging.critical('Barrier direction must be up, right, left or down')
            raise
        self.position=(x,y)
        self.direction=direction
        self.length=length
        self.position2=tuple(
                        map(
                         sum, zip( self.position,tuple([length*x for x in vdir[direction]]) )
                        )
                       )
        # Normalise "backward" barriers
        if self.direction == left or self.direction == up:
            temppos=self.position
            self.position=self.position2
            self.position2=temppos
            if self.direction == left:
                self.direction=right
            else:
                self.direction=down

    def __eq__(self, other):
        return self.position == other.position and self.direction == other.direction and self.length == other.length

    def intersects_with(self,other):
        """Determine if two barriers intersect each other"""
        # Barriers in the same direction
        if self.direction == other.direction:
            if self.direction == right:
                return self.position[1]==other.position[1] and \
                       not ( self.position2[0]<=other.position[0] or \
                             other.position2[0]<=self.position[0] )
            else:
                return self.position[0]==other.position[0] and \
                       not ( self.position2[1]<=other.position[1] or \
                             other.position2[1]<=self.position[1] )
        
        # Orthogonal barriers
        if self.direction == right:
            return ( self.position[0]<other.position[0]<self.position2[0] and \
                     other.position[1]<self.position[1]<other.position2[1] )
        else:
            return ( self.position[1]<other.position[1]<self.position2[1] and \
                     other.position[0]<self.position[0]<other.position2[0] )

    def node(self,i):
        """Return the coordinates of the (i+1)-th barrier node"""
        return tuple( map(sum, zip( self.position,tuple([i*x for x in vdir[self.direction]]) ) ) )

    def nodes(self):
        """Return a list of barrier nodes"""
        return [ self.node(i) for i in range(self.length) ]

class Board:
    """Board class with barriers and table of allowed moves"""
    def __init__(self,side):
        self.side = side
        self.middle = self.side/2
        self.moves = [[up | down | right | left for i in range(self.side)] for j in range(self.side)]
        for i in range(side):
            self.moves[0][i]      &= ~left
            self.moves[side-1][i] &= ~right
            self.moves[i][0]      &= ~up
            self.moves[i][side-1] &= ~down
        self.barriers=[]

    def is_pawn_position_legal(self,x,y):
        """Check if the proposed pawn position is within the board limits"""
        return ( 0 <= x < self.side and 0 <= y < self.side)

    def is_move_allowed(self,position,direction):
        """Check if the proposed move is allowed by barriers"""
        return ( self.moves[position[0]][position[1]] & direction )

    def is_barrier_legal(self,barrier):
        """Check if both ends of the proposed barrier are within the board
        limits"""
        x,y=barrier.position
        x2,y2=barrier.position2
        if barrier.direction == right:
            return ( 0 <= x <= self.side and 0 < y < self.side and 0 <= x2 <= self.side )
        else:
            return ( 0 < x < self.side and 0 <= y <= self.side and 0 <= y2 <= self.side )

    def check_barrier(self,barrier):
        """Check if barrier is allowed"""

        # Check if the barrier is allowed
        if not self.is_barrier_legal( barrier ):
            return False

        # Check if new barrier overlaps with existing barriers
        for oldbarrier in self.barriers:
            if barrier.intersects_with(oldbarrier): return False

        # Barrier is good
        return True

    def are_pawns_closed_off(self):
        """Check if any of the pawns are sealed off (not allowed by the
        rules)"""

        for p in self.pp:
            d = self.distance_to_goal(p)
            if d < 0:
                logging.debug('%s %d %d %d', p.h, p.position[0], p.position[1], d)
                return True
            #if self.distance_to_goal(p.position,p.goal) < 0: return True

        return False

    def init_dist(self, g, moves_status):

        dist = [ [ -1 for x in range(self.side) ] for y in range(self.side) ]
        if g == down:
            for x in range(self.side):
                dist[x][self.side-1] = 0
                moves_status[x][self.side-1] |= enqueued
            queue = deque([(x, self.side-1) for x in range(self.side)])
        elif g == left:
            for y in range(self.side):
                dist[0][y] = 0
                moves_status[0][y] |= enqueued
            queue = deque([(0, y) for y in range(self.side)])
        elif g == up:
            for x in range(self.side):
                dist[x][0] = 0
                moves_status[x][0] |= enqueued
            queue = deque([(x, 0) for x in range(self.side)])
        elif g == right:
            for y in range(self.side):
                dist[self.side-1][y] = 0
                moves_status[self.side-1][y] |= enqueued
            queue = deque([(self.side-1, y) for y in range(self.side)])

        self.bfs(queue, dist, moves_status)

        return dist

    def bfs(self, queue, dist, moves_status):
        """Breadth-first search of the shortest path to any board square."""

        logging.debug("bfs: queue = %s", repr(queue))
        while queue:

#            if not hasattr(self, 'notfirst'):
#                for x in range(self.side):
#                    logging.debug('%s', repr(dist[x]))

            p = queue.popleft()
            for y in range(self.side):
                logging.debug("bfs: dist, moves_status = %s\t%s", repr([dist[x][y] for x in range(self.side)]), repr([moves_status[x][y] for x in range(self.side)]))
            logging.debug("")
#            if p == pf:
#                break
            moves_status[p[0]][p[1]] |= visited

            if self.moves[p[0]][p[1]] & up and not moves_status[p[0]][p[1]-1] & visited_or_enqueued:
                queue.append( (p[0],p[1]-1) )
                moves_status[p[0]][p[1]-1] |= enqueued
                dist[p[0]][p[1]-1] = dist[p[0]][p[1]] + 1
            if self.moves[p[0]][p[1]] & right and not moves_status[p[0]+1][p[1]] & visited_or_enqueued:
                queue.append( (p[0]+1,p[1]) )
                moves_status[p[0]+1][p[1]] |= enqueued
                dist[p[0]+1][p[1]] = dist[p[0]][p[1]] + 1
            if self.moves[p[0]][p[1]] & down and not moves_status[p[0]][p[1]+1] & visited_or_enqueued:
                queue.append( (p[0],p[1]+1) )
                moves_status[p[0]][p[1]+1] |= enqueued
                dist[p[0]][p[1]+1] = dist[p[0]][p[1]] + 1
            if self.moves[p[0]][p[1]] & left and not moves_status[p[0]-1][p[1]] & visited_or_enqueued:
                queue.append( (p[0]-1,p[1]) )
                moves_status[p[0]-1][p[1]] |= enqueued
                dist[p[0]-1][p[1]] = dist[p[0]][p[1]] + 1

        #self.clean_moves()
#        if not hasattr(self, 'notfirst'):
#            self.notfirst = True
#            logging.debug('result of first BFS search:')
#            for x in range(self.side):
#                logging.debug('%s', repr(dist[x]))
                
        return dist

    def clean_moves(self):
        # Clean up
        for x in range(self.side):
            for y in range(self.side):
                self.moves[x][y] &= mask

    def add_barrier_to_map(self, barrier):
        """Update the moves map with the new barrier"""
        for pos in barrier.nodes():
            if barrier.direction == right:
                self.moves[pos[0]][pos[1]-1] &= ~down
                self.moves[pos[0]][pos[1]]   &= ~up
            else:
                self.moves[pos[0]-1][pos[1]] &= ~right
                self.moves[pos[0]][pos[1]]   &= ~left

    def remove_barrier_from_map(self, barrier):
        """Remove the barrier from the allowed moves"""
        for pos in barrier.nodes():
            if barrier.direction == right:
                self.moves[pos[0]][pos[1]-1] |= down
                self.moves[pos[0]][pos[1]]   |= up
            else:
                self.moves[pos[0]-1][pos[1]] |= right
                self.moves[pos[0]][pos[1]]   |= left

    def check_win(self, h):
        p = filter(lambda p: p.h==h, self.pp)[0]
        if (p.goal == up and p.position[1] == 0) or \
            (p.goal == right and p.position[0] == self.side-1) or \
            (p.goal == down and p.position[1] == self.side-1) or \
            (p.goal == left and p.position[0] == 0):
               return True
        else:
            return False


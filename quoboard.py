#!/usr/bin/env python

# For debugging!
import pdb

# Set up logging
import logging, os.path
logging.basicConfig(level=logging.DEBUG,
        format='%(asctime)s %(levelname)-8s %(message)s',
        datefmt='%a, %d %b %Y %H:%M:%S',
        filename=os.path.expanduser('~/.quoserver.log'))


# Global variables
global up, right, down, left, visited
global vdir

up=1
right=2
down=4
left=8
visited=16  # used in Board.closedOffPawns()
vdir={
                up:     (0,-1),
                right:  (1,0),
                down:   (0,1),
                left:   (-1,0)
            }


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
            self.movesCO = [ line[:] for line in self.moves[:] ]
            #if p.position == (0,4): pdb.set_trace()
            if not self.can_win(p.position,p.goal): return True

        return False

    def can_win(self,p,g):
        """Recursive function to determine if position p is connected with the
        g side of the board"""
        if g == up:
            if p[1]==0: return True
        elif g == right:
            if p[0]==self.side-1: return True
        elif g == down:
            if p[1]==self.side-1: return True
        elif g == left:
            if p[0]==0: return True

        self.movesCO[p[0]][p[1]] |= visited

        can=False

        if self.movesCO[p[0]][p[1]] & up and not self.movesCO[p[0]][p[1]-1] & visited:
            can |= self.can_win((p[0],p[1]-1),g)
        if self.movesCO[p[0]][p[1]] & right and not self.movesCO[p[0]+1][p[1]] & visited:
            can |= self.can_win((p[0]+1,p[1]),g)
        if self.movesCO[p[0]][p[1]] & down and not self.movesCO[p[0]][p[1]+1] & visited:
            can |= self.can_win((p[0],p[1]+1),g)
        if self.movesCO[p[0]][p[1]] & left and not self.movesCO[p[0]-1][p[1]] & visited:
            can |= self.can_win((p[0]-1,p[1]),g)

        return can

    def add_barrier(self,barrier):
        """Add a new barrier if allowed"""
        if self.check_barrier(barrier):
            self.add_barrier_to_map(barrier)
            # Check if new barrier closes off one of the pawns
            if self.are_pawns_closed_off():
                self.remove_barrier_from_map(barrier)
                logging.info("Barrier %s, %d, len=%d closes off some pawns, rejected", str(barrier.position), barrier.direction, barrier.length)
                return False
            else:
                self.barriers.append(barrier)
                return True
        else:
            logging.info("Barrier %s, %d, len=%d is illegal, rejected", str(barrier.position), barrier.direction, barrier.length)
            return False

    def add_barrier_to_map(self,barrier):
        """Update the moves map with the new barrier"""
        for pos in barrier.nodes():
            if barrier.direction == right:
                self.moves[pos[0]][pos[1]-1] &= ~down
                self.moves[pos[0]][pos[1]]   &= ~up
            else:
                self.moves[pos[0]-1][pos[1]] &= ~right
                self.moves[pos[0]][pos[1]]   &= ~left

    def remove_barrier_from_map(self,barrier):
        """Remove the barrier from the allowed moves"""
        for pos in barrier.nodes():
            if barrier.direction == right:
                self.moves[pos[0]][pos[1]-1] |= down
                self.moves[pos[0]][pos[1]]   |= up
            else:
                self.moves[pos[0]-1][pos[1]] |= right
                self.moves[pos[0]][pos[1]]   |= left


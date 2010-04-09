#!/usr/bin/env python

# For debugging!
import pdb

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

class Barrier:
    """Barrier class"""
    # Barrier positions are defined as being (0,0) in the top-left corner
    # of the board. Thus each coordinate ranges from 0 to side
    def __init__(self,x,y,direction,length=2):
        if direction!=up and direction!=right and direction!=down and direction!=left : raise 'Barrier direction must be up, right, left or down'
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

    def intersectsWith(self,other):
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
        #if side%2 == 0: raise 'Board objects must have odd side length'
        self.side = side
        self.middle = self.side/2
        self.moves = [[up | down | right | left for i in range(self.side)] for j in range(self.side)]
        for i in range(side):
            self.moves[0][i]      &= ~left
            self.moves[side-1][i] &= ~right
            self.moves[i][0]      &= ~up
            self.moves[i][side-1] &= ~down
        self.barriers=[]

    def checkBarrier(self,barrier):
        """Check if barrier is allowed"""

        # Check if the barrier origin is in an allowed position
        if barrier.position[0]<0 or barrier.position[0]>self.side or barrier.position[1]<0 or barrier.position[1]>self.side:
            return False
        # Check if the whole barrier is contained in the board
        if barrier.position2[0]<0 or barrier.position2[0]>self.side or barrier.position2[1]<0 or barrier.position2[1]>self.side:
            return False

        # Check if new barrier overlaps with existing barriers
        for oldbarrier in self.barriers:
            if barrier.intersectsWith(oldbarrier): return False

        # Barrier is good
        return True

    def closedOffPawns(self):
        """Check if any of the pawns are sealed off (not allowed by the
        rules)"""

        for p in self.pp:
            self.movesCO = [ line[:] for line in self.moves[:] ]
            #if p.position == (0,4): pdb.set_trace()
            if not self.canWin(p.position,p.goal): return True

        return False

    def canWin(self,p,g):
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
            can |= self.canWin((p[0],p[1]-1),g)
        if self.movesCO[p[0]][p[1]] & right and not self.movesCO[p[0]+1][p[1]] & visited:
            can |= self.canWin((p[0]+1,p[1]),g)
        if self.movesCO[p[0]][p[1]] & down and not self.movesCO[p[0]][p[1]+1] & visited:
            can |= self.canWin((p[0],p[1]+1),g)
        if self.movesCO[p[0]][p[1]] & left and not self.movesCO[p[0]-1][p[1]] & visited:
            can |= self.canWin((p[0]-1,p[1]),g)

        return can

    def addBarrier(self,barrier):
        """Add a new barrier if allowed"""
        if self.checkBarrier(barrier):
            self.addBarrierToMap(barrier)
            # Check if new barrier closes off one of the pawns
            if self.closedOffPawns():
                self.removeBarrierFromMap(barrier)
                print "Barrier ", barrier.position, barrier.direction, " closes off some pawns, rejected"
                return False
            else:
                self.barriers.append(barrier)
                return True
        else:
            print "Illegal barrier ", barrier.position, barrier.direction, " rejected"
            return False

    def addBarrierToMap(self,barrier):
        """Update the moves map with the new barrier"""
        for pos in barrier.nodes():
            if barrier.direction == right:
                self.moves[pos[0]][pos[1]-1] &= ~down
                self.moves[pos[0]][pos[1]]   &= ~up
            else:
                self.moves[pos[0]-1][pos[1]] &= ~right
                self.moves[pos[0]][pos[1]]   &= ~left

    def removeBarrierFromMap(self,barrier):
        """Remove the barrier from the allowed moves"""
        for pos in barrier.nodes():
            if barrier.direction == right:
                self.moves[pos[0]][pos[1]-1] |= down
                self.moves[pos[0]][pos[1]]   |= up
            else:
                self.moves[pos[0]-1][pos[1]] |= right
                self.moves[pos[0]][pos[1]]   |= left

    def prettyPrintASCII(self):
        """Pretty-print the board in ASCII"""
        cellsizex=6 # must be >2 and even
        cellsizey=4 # must be >2 and even
        side=self.side
        image=[(cellsizex*side+1)*' ' for y in range(cellsizey*side+1)]

        # Horizontal lines
        for y in range(0,cellsizey*side,cellsizey):
            image[y] = side * ('+' + (cellsizex-1)*'-') + '+'
        image[cellsizey*side] = side * ('+' + (cellsizex-1)*'-') + '+'

        # Vertical lines
        for y in range(cellsizey*side+1):
            if y%cellsizey==0: continue
            for x in range(cellsizex,cellsizex*(side+1),cellsizex):
                image[y]=image[y][:x]+'|'+image[y][x+1:]
                image[y]='|'+image[y][1:]

        # Pawns
        for p in self.pp:
            x = cellsizex / 2 + p.position[0]*cellsizex
            y = cellsizey / 2 + p.position[1]*cellsizey
            image[y] = image[y][:x] + p.symbol + image[y][x+1:]

        # Barriers
        for b in self.barriers:
            p=b.node(0)
            x = p[0]*cellsizex
            y = p[1]*cellsizey
            if b.direction == right:
                for i in range(1,b.length*cellsizex):
                    x += 1
                    image[y] = image[y][:x] + 'X' + image[y][x+1:]
            else:
                for i in range(1,b.length*cellsizey):
                    y += 1
                    image[y] = image[y][:x] + 'X' + image[y][x+1:]

        # Arrows
        for x in range(self.side):
            for y in range(self.side):
                if self.moves[x][y] & up:
                    xa = cellsizex / 2 + x*cellsizex
                    ya = cellsizey / 2 + y*cellsizey - 1
                    image[ya] = image[ya][:xa] + '^' + image[ya][xa+1:]
                if self.moves[x][y] & right:
                    xa = cellsizex / 2 + x*cellsizex + 1
                    ya = cellsizey / 2 + y*cellsizey
                    image[ya] = image[ya][:xa] + '>' + image[ya][xa+1:]
                if self.moves[x][y] & down:
                    xa = cellsizex / 2 + x*cellsizex
                    ya = cellsizey / 2 + y*cellsizey + 1
                    image[ya] = image[ya][:xa] + 'v' + image[ya][xa+1:]
                if self.moves[x][y] & left:
                    xa = cellsizex / 2 + x*cellsizex - 1
                    ya = cellsizey / 2 + y*cellsizey
                    image[ya] = image[ya][:xa] + '<' + image[ya][xa+1:]

        # Do the drawing
        for line in image: print line


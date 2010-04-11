#!/usr/bin/env python

import quoboard
import random
global up,right,down,left,vdir
vdir = quoboard.vdir
up = quoboard.up
right = quoboard.right
down = quoboard.down
left = quoboard.left

class Pawn:
    """Pawn class"""
    def __init__(self,x,y,symbol,goal):
        self.position=(x,y)
        self.symbol=symbol
        self.goal=goal
        alphabet='abcdefghijklmnopqrstuvwxyz'
        self.h=reduce(lambda a,b:a+b, [ random.choice(alphabet) for i in range(15) ] )

    def move(self,direction):
       self.position=tuple(map(sum,zip(self.position,quoboard.vdir[direction])))
       return self.position

class ServerBoard(quoboard.Board):
    """Board class to be used by server applications
    Includes methods to add barriers and update the table of allowed moves"""

    def __init__(self,side=9,nplayers=4):
        """A simple constructor, performs some sanity checks"""
        if nplayers < 2 or nplayers > 4: raise 'Barrier length must be >0 and <side length'
        quoboard.Board.__init__(self,side)

        initialised=False
        while(not initialised):
            self.pp = [Pawn(self.middle, 0, '1', down)]
            self.nplayers=nplayers
            if self.nplayers == 2:
                self.pp.append(Pawn(self.middle, self.side-1, '2', up))
            elif self.nplayers == 3:
                self.pp.append(Pawn(self.side-1, self.middle, '2', left))
                self.pp.append(Pawn(self.middle, self.side-1, '3', up))
            elif self.nplayers == 4:
                self.pp.append(Pawn(self.side-1, self.middle, '2', left))
                self.pp.append(Pawn(self.middle, self.side-1, '3', up))
                self.pp.append(Pawn(0, self.middle, '4', right))
            # Check that the hashes are all different
            # (usually overkill, but anyway...)
            initialised=True
            hs = [ p.h for p in self.pp ]
            for h in hs:
                if hs.count(h) > 1: initialised=False



MyServerBoard=ServerBoard()
for i in range(60):
    MyServerBoard.addBarrier(quoboard.Barrier(
        random.randint(0,MyServerBoard.side-1),
        random.randint(0,MyServerBoard.side-1),
        random.choice([up,right,down,left]),
        2))
MyServerBoard.prettyPrintASCII()

#!/usr/bin/env python

from quoboard import *

class Pawn:
    """Pawn class"""
    def __init__(self,x,y,symbol,goal):
        self.position=(x,y)
        self.symbol=symbol
        self.goal=goal

class ServerBoard(Board):
    """Board class to be used by server applications
    Includes methods to add barriers and update the table of allowed moves"""

    def __init__(self,side=9,nplayers=4):
        """A simple constructor, performs some sanity checks"""
        if nplayers < 2 or nplayers > 4: raise 'Barrier length must be >0 and <side length'
        Board.__init__(self,side)
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


MyServerBoard=ServerBoard()
MyServerBoard.addBarrier(Barrier(2,3,down,2))
MyServerBoard.prettyPrintASCII()

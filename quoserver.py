#!/usr/bin/env python

import quoboard
import random
import curses.wrapper
import time


# Global variables
global up,right,down,left,vdir
vdir = quoboard.vdir
up = quoboard.up
right = quoboard.right
down = quoboard.down
left = quoboard.left
logging = quoboard.logging

# Class definitions

class Pawn:
    """Pawn class"""

    def __init__(self,x,y,symbol,goal,ai):
        self.position=(x,y)
        self.symbol=symbol
        self.goal=goal
        self.ai=ai
        alphabet='abcdefghijklmnopqrstuvwxyz'
        self.h=reduce(lambda a,b:a+b, [ random.choice(alphabet) for i in range(15) ] )

    def move(self,position):
       self.position=position
       return self.position

class ServerBoard(quoboard.Board):
    """Board class to be used by server applications.

    Includes methods to add barriers and update the table of allowed moves"""

    def __init__(self,side,nplayers,player_ai):
        """A simple constructor, performs some sanity checks"""
        if nplayers < 2 or nplayers > 4:
            logging.critical('Barrier length must be >0 and <side length')
            raise
        quoboard.Board.__init__(self,side)

        initialised=False
        while(not initialised):
            self.pp = [Pawn(self.middle, 0, '1', down, player_ai[0])]
            self.nplayers=nplayers
            if self.nplayers == 2:
                self.pp.append(Pawn(self.middle, self.side-1, '2', up, player_ai[1]))
            elif self.nplayers == 3:
                self.pp.append(Pawn(self.side-1, self.middle, '2', left, player_ai[1]))
                self.pp.append(Pawn(self.middle, self.side-1, '3', up, player_ai[2]))
            elif self.nplayers == 4:
                self.pp.append(Pawn(self.side-1, self.middle, '2', left, player_ai[1]))
                self.pp.append(Pawn(self.middle, self.side-1, '3', up, player_ai[2]))
                self.pp.append(Pawn(0, self.middle, '4', right, player_ai[3]))
            # Check that the hashes are all different
            # (usually overkill, but anyway...)
            initialised=True
            hs = [ p.h for p in self.pp ]
            for h in hs:
                if hs.count(h) > 1: initialised=False

    def move_pawn(self,h,direction):
        """Check if the proposed move is allowed for the pawn identified by
        hash h"""

        pl=filter(lambda q: h==q.h, self.pp)
        if len(pl)==0:
            logging.critical("Hash %s not recognized", h)
            raise

        p=pl[0]
        posnew=tuple( map(sum, zip( p.position, vdir[direction]) ) )
        if self.is_pawn_position_legal(*posnew) and self.is_move_allowed(p.position,direction):
            p.move(posnew)
            return True
        else:
            return False

class QuoServer:

    def __init__(self):

        self.read_config()

        self.serverboard=ServerBoard(self.side,self.nplayers,self.player_ai)
        if self.curses_ui:
            curses.wrapper(self.main_loop)
        else:
            self.main_loop(None)

    def main_loop(self,stdscr):
        """The main loop of the game."""

        if self.curses_ui:
            self.stdscr=stdscr
            self.curses_init()

        while(True):
            for i in range(self.nplayers):
                self.pretty_print()
                if self.check_win(i):
                    self.win(i)
                    return
                if self.serverboard.pp[i].ai:
                    while(not self.serverboard.move_pawn(self.serverboard.pp[i].h,
                        random.choice([up,right,down,left]))):
                        pass
                else:
                    moved=False
                    while(not moved):
                        c = self.getinput()
                        if c == ord('q'): return
                        elif c == curses.KEY_LEFT:
                            moved = self.serverboard.move_pawn(self.serverboard.pp[i].h, left)
                        elif c == curses.KEY_RIGHT:
                            moved = self.serverboard.move_pawn(self.serverboard.pp[i].h, right)
                        elif c == curses.KEY_UP:
                            moved = self.serverboard.move_pawn(self.serverboard.pp[i].h, up)
                        elif c == curses.KEY_DOWN:
                            moved = self.serverboard.move_pawn(self.serverboard.pp[i].h, down)
                        elif c == ord('b'):
                            moved = self.choose_barrier()
                        if not moved: curses.flash()

    def choose_barrier(self):
        """Choose where to put the barrier on the map."""

        # First choose the barrier position
        pos_curs=[self.serverboard.middle,self.serverboard.middle]
        chosen_position=False
        while not chosen_position:
            oldp=pos_curs[:]

            x = self.ox + pos_curs[0]*self.cellsizex
            y = self.oy + pos_curs[1]*self.cellsizey
            oldc=self.stdscr.inch(y,x)
            logging.info('oldc: %d',oldc)
            self.stdscr.addch(y,x,ord('X'), curses.color_pair(4) | curses.A_REVERSE )
            self.stdscr.refresh()

            c = self.getinput()
            if c == ord('q'):
                x = self.ox + oldp[0]*self.cellsizex
                y = self.oy + oldp[1]*self.cellsizey
                self.stdscr.addch(y,x,ord(' '), curses.color_pair(4) )
                return False
            elif c == curses.KEY_LEFT:
                pos_curs[0]=max(0,pos_curs[0]-1)
            elif c == curses.KEY_RIGHT:
                pos_curs[0]=min(self.side,pos_curs[0]+1)
            elif c == curses.KEY_UP:
                pos_curs[1]=max(0,pos_curs[1]-1)
            elif c == curses.KEY_DOWN:
                pos_curs[1]=min(self.side,pos_curs[1]+1)
            elif c == ord('b') or c == curses.KEY_ENTER:
                chosen_position=True

            x = self.ox + oldp[0]*self.cellsizex
            y = self.oy + oldp[1]*self.cellsizey
            self.stdscr.addch(y, x, oldc & 255, oldc ^ (oldc & 255) )

        # Now choose the barrier orientation
        length=2
        if pos_curs[0]<self.side-length+1:
            direction=right
        else:
            direction=left
        chosen_direction=False

        while not chosen_direction:
            oldd=direction
            oldc=[]

            x = self.ox + pos_curs[0]*self.cellsizex
            y = self.oy + pos_curs[1]*self.cellsizey
            if direction == right:
                for i in range(1,length*self.cellsizex):
                    x += 1
                    oldc.append(self.stdscr.inch(y,x))
                    self.stdscr.addch(y,x,ord('X'), curses.color_pair(4) | curses.A_REVERSE )
            elif direction == down:
                for i in range(1,length*self.cellsizey):
                    y += 1
                    oldc.append(self.stdscr.inch(y,x))
                    self.stdscr.addch(y,x,ord('X'), curses.color_pair(4) | curses.A_REVERSE )
            elif direction == left:
                for i in range(1,length*self.cellsizex):
                    x -= 1
                    oldc.append(self.stdscr.inch(y,x))
                    self.stdscr.addch(y,x,ord('X'), curses.color_pair(4) | curses.A_REVERSE )
            elif direction == up:
                for i in range(1,length*self.cellsizey):
                    y -= 1
                    oldc.append(self.stdscr.inch(y,x))
                    self.stdscr.addch(y,x,ord('X'), curses.color_pair(4) | curses.A_REVERSE )
            self.stdscr.refresh()

            c = self.getinput()
            if c == ord('q'):
                x = self.ox + pos_curs[0]*self.cellsizex
                y = self.oy + pos_curs[1]*self.cellsizey
                if direction == right:
                    for i in range(1,length*self.cellsizex):
                        x += 1
                        self.stdscr.addch(y,x,oldc.pop(0), curses.color_pair(4) )
                elif direction == down:
                    for i in range(1,length*self.cellsizey):
                        y += 1
                        self.stdscr.addch(y,x,oldc.pop(0), curses.color_pair(4) )
                elif direction == left:
                    for i in range(1,length*self.cellsizex):
                        x -= 1
                        self.stdscr.addch(y,x,oldc.pop(0), curses.color_pair(4) )
                elif direction == up:
                    for i in range(1,length*self.cellsizey):
                        y -= 1
                        self.stdscr.addch(y,x,oldc.pop(0), curses.color_pair(4) )
                self.stdscr.refresh()

                return False
            elif c == curses.KEY_LEFT:
                if pos_curs[0]>=length:
                    direction=left
                else:
                    curses.flash()
            elif c == curses.KEY_RIGHT:
                if pos_curs[0]<=self.side-length:
                    direction=right
                else:
                    curses.flash()
            elif c == curses.KEY_UP:
                if pos_curs[1]>=length:
                    direction=up
                else:
                    curses.flash()
            elif c == curses.KEY_DOWN:
                if pos_curs[1]<=self.side-length:
                    direction=down
                else:
                    curses.flash()
            elif c == ord('b') or c == curses.KEY_ENTER:
                chosen_direction=True

            x = self.ox + pos_curs[0]*self.cellsizex
            y = self.oy + pos_curs[1]*self.cellsizey
            if oldd == right:
                for i in range(1,length*self.cellsizex):
                    x += 1
                    occ = oldc.pop(0)
                    self.stdscr.addch(y,x, occ & 255 , occ ^ (occ & 255) )
            elif oldd == down:
                for i in range(1,length*self.cellsizey):
                    y += 1
                    occ = oldc.pop(0)
                    self.stdscr.addch(y,x, occ & 255 , occ ^ (occ & 255) )
            elif oldd == left:
                for i in range(1,length*self.cellsizex):
                    x -= 1
                    occ = oldc.pop(0)
                    self.stdscr.addch(y,x, occ & 255 , occ ^ (occ & 255) )
            elif oldd == up:
                for i in range(1,length*self.cellsizey):
                    y -= 1
                    occ = oldc.pop(0)
                    self.stdscr.addch(y,x, occ & 255 , occ ^ (occ & 255) )

        return self.serverboard.add_barrier(quoboard.Barrier(
            pos_curs[0],pos_curs[1],direction,length))



    def check_win(self,i):
        pass

    def win(self,i):
        pass

    def getinput(self):
        """Get input from the user."""
        if self.curses_ui:
            return self.stdscr.getch()
        else:
            logging.critical('Input in ASCII mode: to be implemented')
            raise 

    def demo(self):
        """Demo mode"""
        for i in range(25):
            for j in range(4):
                if not self.serverboard.add_barrier(quoboard.Barrier(
                    random.randint(0,self.serverboard.side-1),
                    random.randint(0,self.serverboard.side-1),
                    random.choice([up,right,down,left]),
                    2)):
                    while(not self.serverboard.move_pawn(self.serverboard.pp[j].h,
                        random.choice([up,right,down,left]))):
                        pass
                self.pretty_print(5,5)
                time.sleep(1)

    def curses_init(self):
        """Initialises the curses system."""
        curses.curs_set(0)
        curses.init_pair(1, curses.COLOR_BLUE, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_GREEN)
        curses.init_pair(4, curses.COLOR_GREEN, curses.COLOR_BLACK)
        self.stdscr.border()

    def read_config(self):
        """Read the configuration file using the ConfigParser module"""

        import ConfigParser
        import os.path
        try:
            cfgfilename=os.path.expanduser('~/.quoserver')
            f=open(cfgfilename,'r')
        except IOError:
            logging.warning('Configuration file %s does not exist, creating a new one', cfgfilename) 
            self.create_default_config(cfgfilename)
            try:
                f=open(cfgfilename,'r')
            except:
                logging.error('Cannot read configuration file %s, bombing out', cfgfilename)
                raise

        config = ConfigParser.RawConfigParser()
        config.readfp(f)
        f.close()

        self.side = config.getint('Board','side')
        self.nplayers = config.getint('Game','nplayers')
        self.player_ai = [ config.getboolean('Game','player'+str(i)+'_ai') for i in range(1,self.nplayers+1) ]
        self.curses_ui = config.getboolean('UI','curses_ui')
        self.cellsizex = max(2,(config.getint('UI','cellsizex')/2)*2)
        self.cellsizey = max(2,(config.getint('UI','cellsizey')/2)*2)
        if self.curses_ui:
            self.pretty_print=self.pretty_print_curses
        else:
            self.pretty_print=self.pretty_print_ascii
            self.curses_ui=False

    def create_default_config(self,cfgfilename):
        """Create a config file with default option values"""
        import ConfigParser
        config = ConfigParser.RawConfigParser()

        # Dictionaries of default options and values
        opt_board = {
            'side':         9
        }
        opt_game = {
            'nplayers':     4,
            'player1_ai':   'off',
            'player2_ai':   'off',
            'player3_ai':   'off',
            'player4_ai':   'off'
        }
        opt_ui = {
            'curses_ui':     'on',
            'cellsizex':     6,
            'cellsizey':     4
        }

        config.add_section('UI')
        config.add_section('Game')
        config.add_section('Board')

        for opt, val in opt_board.items():
            config.set('Board', opt, val)

        for opt, val in opt_game.items():
            config.set('Game', opt, val)

        for opt, val in opt_ui.items():
            config.set('UI', opt, val)

        try:
            f=open(cfgfilename,'w')
        except:
            logging.critical('Cannot open configuration file %s for writing, bombing out', cfgfilename)
            raise

        config.write(f)
        f.close()

    def pretty_print_curses(self):
        """Pretty-print the board using curses"""
        side=self.side
        cellsizex=self.cellsizex
        cellsizey=self.cellsizey
        scr=self.stdscr
        self.ox=5
        self.oy=5
        ox=self.ox
        oy=self.oy
        # Horizontal lines
#        for y in range(0,cellsizey*side,cellsizey):
#            scr.addstr(oy+y,ox, side * (' ' + (cellsizex-1)*' ') + ' ',
#                curses.color_pair(1) | curses.A_REVERSE )
#        scr.addstr(oy+cellsizey*side,ox,side * (' ' + (cellsizex-1)*' ') + ' ',
#            curses.color_pair(1) | curses.A_REVERSE )

        # Vertical lines
#        for y in range(cellsizey*side+1):
#            if y%cellsizey==0: continue
#            for x in range(cellsizex,cellsizex*(side+1),cellsizex):
#                scr.addstr(oy+y,ox+x,' ', curses.color_pair(1) | curses.A_REVERSE )
#                scr.addstr(oy+y,ox,' ', curses.color_pair(1) | curses.A_REVERSE )

        # Squares
        for y in range(cellsizey*side+1):
            if y%cellsizey==0: continue
            for x in range(1,cellsizex*side+1,cellsizex):
                scr.addstr(oy+y,ox+x, (cellsizex-1)*' ',
                    curses.color_pair(1) | curses.A_REVERSE )

        # Pawns
        for p in self.serverboard.pp:
            x = cellsizex / 2 + p.position[0]*cellsizex
            y = cellsizey / 2 + p.position[1]*cellsizey
            scr.addstr(oy+y,ox+x,p.symbol, curses.color_pair(3) )

        # Barriers
        for b in self.serverboard.barriers:
            p=b.node(0)
            x = p[0]*cellsizex
            y = p[1]*cellsizey
            if b.direction == right:
                for i in range(1,b.length*cellsizex):
                    x += 1
                    scr.addstr(oy+y,ox+x,'X', curses.color_pair(2) | curses.A_REVERSE )
            else:
                for i in range(1,b.length*cellsizey):
                    y += 1
                    scr.addstr(oy+y,ox+x,'X', curses.color_pair(2) | curses.A_REVERSE )

        # Arrows
        for x in range(self.side):
            for y in range(self.side):
                if self.serverboard.moves[x][y] & up:
                    xa = cellsizex / 2 + x*cellsizex
                    ya = cellsizey / 2 + y*cellsizey - 1
                    scr.addstr(oy+ya,ox+xa,'^', curses.color_pair(1) | curses.A_REVERSE )
                if self.serverboard.moves[x][y] & right:
                    xa = cellsizex / 2 + x*cellsizex + 1
                    ya = cellsizey / 2 + y*cellsizey
                    scr.addstr(oy+ya,ox+xa,'>', curses.color_pair(1) | curses.A_REVERSE )
                if self.serverboard.moves[x][y] & down:
                    xa = cellsizex / 2 + x*cellsizex
                    ya = cellsizey / 2 + y*cellsizey + 1
                    scr.addstr(oy+ya,ox+xa,'v', curses.color_pair(1) | curses.A_REVERSE )
                if self.serverboard.moves[x][y] & left:
                    xa = cellsizex / 2 + x*cellsizex - 1
                    ya = cellsizey / 2 + y*cellsizey
                    scr.addstr(oy+ya,ox+xa,'<', curses.color_pair(1) | curses.A_REVERSE )

        # Do the drawing
        scr.refresh()

    def pretty_print_ascii(self):
        """Pretty-print the board in ASCII"""
        side=self.side
        cellsizex=self.cellsizex
        cellsizey=self.cellsizey
        ox=0
        oy=0

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
        for p in self.serverboard.pp:
            x = cellsizex / 2 + p.position[0]*cellsizex
            y = cellsizey / 2 + p.position[1]*cellsizey
            image[y] = image[y][:x] + p.symbol + image[y][x+1:]

        # Barriers
        for b in self.serverboard.barriers:
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
                if self.serverboard.moves[x][y] & up:
                    xa = cellsizex / 2 + x*cellsizex
                    ya = cellsizey / 2 + y*cellsizey - 1
                    image[ya] = image[ya][:xa] + '^' + image[ya][xa+1:]
                if self.serverboard.moves[x][y] & right:
                    xa = cellsizex / 2 + x*cellsizex + 1
                    ya = cellsizey / 2 + y*cellsizey
                    image[ya] = image[ya][:xa] + '>' + image[ya][xa+1:]
                if self.serverboard.moves[x][y] & down:
                    xa = cellsizex / 2 + x*cellsizex
                    ya = cellsizey / 2 + y*cellsizey + 1
                    image[ya] = image[ya][:xa] + 'v' + image[ya][xa+1:]
                if self.serverboard.moves[x][y] & left:
                    xa = cellsizex / 2 + x*cellsizex - 1
                    ya = cellsizey / 2 + y*cellsizey
                    image[ya] = image[ya][:xa] + '<' + image[ya][xa+1:]

        # Do the drawing
        for line in image: print line

my_quoridor_server=QuoServer()


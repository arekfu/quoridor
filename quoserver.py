#!/usr/bin/env python

import quoboard, quoui, quoaiengine
import random, time, curses.wrapper, copy

from quoboard import up, right, down, left, vdir, logging




# Class definitions

class Pawn:
    """Pawn class"""

    def __init__(self,x,y,symbol,goal,ai):
        self.position=(x,y)
        self.symbol=symbol
        self.goal=goal
        alphabet='abcdefghijklmnopqrstuvwxyz'
        self.h=reduce(lambda a,b:a+b, [ random.choice(alphabet) for i in range(15) ] )
        if ai:
            self.ai = quoaiengine.QuoAIEngine(self.h)
        else:
            self.ai = None

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

        # Check if pawn can go there
        if not self.is_pawn_position_legal(*posnew) or not self.is_move_allowed(p.position,direction):
            return False

        # Jumping over another pawn?
        if any( [ posnew == self.pp[i].position for i in range(self.nplayers) if self.pp[i].h != h ] ):
            posnew2=tuple( map(sum, zip( posnew, vdir[direction]) ) )
            # Check if pawn can go there
            if not self.is_pawn_position_legal(*posnew2):
                return False
            elif not self.is_move_allowed(posnew,direction):
                # Here we should implement the "bounce move", i.e. jump off a
                # wall and land next to the other pawn. For the moment the move
                # is just forbidden.
                return False
            # Do not jump two pawns in a row
            if any( [ posnew2 == self.pp[i].position for i in range(self.nplayers) if self.pp[i].h != h ] ):
                return False

            p.move(posnew2)
            return True

        else:   # Not jumping over other pawns
            p.move(posnew)
            return True

class QuoServer:

    def __init__(self):

        global the_server

        self.read_config()

        self.serverboard=ServerBoard(self.side,self.nplayers,self.player_ai)
        self.ui = quoui.ui_curses(self.side,self.cellsizex,self.cellsizey,self.nplayers,self)

        curses.wrapper(self.main_loop)

    def main_loop(self,scr):
        """The main loop of the game."""

        self.ui.do_init(scr)

        while(True):
            for i in range(self.nplayers):
                self.ui.draw_board(self.serverboard.pp, self.serverboard.barriers)
                self.ui.draw_players_win(self.serverboard.pp, self.serverboard.pp[i].h)
                if self.serverboard.pp[i].ai:
                    #while(not self.serverboard.move_pawn(self.serverboard.pp[i].h,
                    #    random.choice([up,right,down,left]))):
                    #    pass
                    self.serverboard.pp[i].ai.get_move(copy.deepcopy(self.serverboard))
                else:
                    moved=False
                    while(not moved):
                        c = self.ui.get_input()
                        if c == self.ui.inp.quit: return
                        elif c == self.ui.inp.left:
                            moved = self.serverboard.move_pawn(self.serverboard.pp[i].h, left)
                        elif c == self.ui.inp.right:
                            moved = self.serverboard.move_pawn(self.serverboard.pp[i].h, right)
                        elif c == self.ui.inp.up:
                            moved = self.serverboard.move_pawn(self.serverboard.pp[i].h, up)
                        elif c == self.ui.inp.down:
                            moved = self.serverboard.move_pawn(self.serverboard.pp[i].h, down)
                        elif c == self.ui.inp.barrier:
                            moved = self.choose_barrier()
                        if not moved:
                            self.ui.communicate("Illegal move, P" + self.serverboard.pp[i].symbol + "!\n")
                            self.ui.warn()
                if self.check_win(i):
                    self.win(i)
                    return

    def update_screen(self):
        """Call all the methods that update the screen graphics."""
        self.ui.draw_board(self.serverboard.pp, self.serverboard.barriers)
        self.ui.clear_panel()
        self.ui.clear_players_win()

    def choose_barrier(self):
        """Choose where to put the barrier on the map."""

        # First choose the barrier position
        pos_curs=[self.serverboard.middle,self.serverboard.middle]
        chosen_position=False
        while not chosen_position:

            self.ui.draw_barrier_cursor(*pos_curs)

            c = self.ui.get_input()
            if c == self.ui.inp.quit:
                self.ui.delete_old_barrier_cursor(True)
                return False
            elif c == self.ui.inp.left:
                pos_curs[0]=max(0,pos_curs[0]-1)
            elif c == self.ui.inp.right:
                pos_curs[0]=min(self.side,pos_curs[0]+1)
            elif c == self.ui.inp.up:
                pos_curs[1]=max(0,pos_curs[1]-1)
            elif c == self.ui.inp.down:
                pos_curs[1]=min(self.side,pos_curs[1]+1)
            elif c == self.ui.inp.barrier:
                chosen_position=True

        self.ui.delete_old_barrier_cursor(False)
        # Now choose the barrier orientation
        length=2
        if pos_curs[0]<self.side-length+1:
            direction=right
        else:
            direction=left
        chosen_direction=False

        while not chosen_direction:
            self.ui.draw_barrier(pos_curs[0],pos_curs[1],direction,length)

            c = self.ui.get_input()
            if c == self.ui.inp.quit:
                self.ui.delete_old_barrier(True)
                return False
            elif c == self.ui.inp.left:
                if pos_curs[0]>=length:
                    direction=left
                else:
                    self.ui.warn()
            elif c == self.ui.inp.right:
                if pos_curs[0]<=self.side-length:
                    direction=right
                else:
                    self.ui.warn()
            elif c == self.ui.inp.up:
                if pos_curs[1]>=length:
                    direction=up
                else:
                    self.ui.warn()
            elif c == self.ui.inp.down:
                if pos_curs[1]<=self.side-length:
                    direction=down
                else:
                    self.ui.warn()
            elif c == self.ui.inp.barrier:
                chosen_direction=True

        result= self.serverboard.add_barrier(quoboard.Barrier(
            pos_curs[0],pos_curs[1],direction,length))
        self.ui.delete_old_barrier(not result)
        return result

    def check_win(self,i):
        p = self.serverboard.pp[i]
        if (p.goal == up and p.position[1] == 0) or \
            (p.goal == right and p.position[0] == self.side-1) or \
            (p.goal == down and p.position[1] == self.side-1) or \
            (p.goal == left and p.position[0] == 0):
               return True
        else:
            return False
        pass

    def win(self,i):
        pass

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
        self.cellsizex = max(2,(config.getint('UI','cellsizex')/2)*2)
        self.cellsizey = max(2,(config.getint('UI','cellsizey')/2)*2)

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



my_quoridor_server=QuoServer()


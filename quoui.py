#!/usr/bin/env python

import curses, curses.wrapper, signal

from quoboard import up, right, down, left, vdir, logging



def sigwinch_handler(n,frame):
    """Signal handler for terminal resize events."""
    global the_ui
    logging.debug('SIGWINCH event, refreshing curses layer')
    curses.endwin()
    curses.initscr()
    the_ui.update_win_size()






class ui_curses:
    """User interface using curses."""

    def __init__(self,side,cx,cy,npl):
        global the_ui
        self.side=side
        self.cellsizex=cx
        self.cellsizey=cy
        self.nplayers=npl
        the_ui=self

        # Set up the SIGWINCH handler
        signal.signal(signal.SIGWINCH,sigwinch_handler)

    def update_win_size(self):
        self.scr_hei, self.scr_wid = self.scr.getmaxyx()
        self.boardw_wid, self.boardw_hei = 2 * (self.scr_wid - 2) / 3, self.scr_hei - 2
        self.panelw_wid, self.panelw_hei = self.scr_wid - 2 - self.boardw_wid, self.scr_hei - 2
        self.boardw_ox, self.boardw_oy = 1, 1
        self.panelw_ox, self.panelw_oy = self.boardw_ox + self.boardw_wid, 1
        self.board_win = self.scr.subwin(self.boardw_hei, self.boardw_wid, self.boardw_oy, self.boardw_ox)
        self.panel_win = self.scr.subwin(self.panelw_hei, self.panelw_wid, self.panelw_oy, self.panelw_ox)
        logging.debug('ui_curses.update_win_size: scr_wid, scr_hei = %d x %d', self.scr_wid, self.scr_hei)
        logging.debug('                           boardw_wid, boardw_hei = %d x %d', self.boardw_wid, self.boardw_hei)
        logging.debug('                           panelw_wid, panelw_hei = %d x %d', self.panelw_wid, self.panelw_hei)

    def do_init(self,scr):
        """Initialises the curses system."""
        self.scr=scr
        curses.curs_set(0)
        curses.init_pair(1, curses.COLOR_BLUE, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_GREEN)
        curses.init_pair(4, curses.COLOR_GREEN, curses.COLOR_BLACK)
        self.scr.border()

        self.update_win_size()

    class inp:
        """Subclass for input codes."""
        up = curses.KEY_UP
        down = curses.KEY_DOWN
        left = curses.KEY_LEFT
        right = curses.KEY_RIGHT
        quit = ord('q')
        barrier = ord('b')

    def draw_board(self, pp, barriers):
        """Pretty-print the board using curses"""
        side=self.side
        cellsizex=self.cellsizex
        cellsizey=self.cellsizey
        scr=self.board_win

        board_wid = side * cellsizex + 1
        board_hei = side * cellsizey + 1

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
            if y>=self.boardw_hei: break
            for x in range(1,cellsizex*side+1,cellsizex):
                if x>=self.boardw_wid: break
                scr.addnstr(y, x, (cellsizex-1)*' ', self.boardw_wid-x,
                    curses.color_pair(1) | curses.A_REVERSE )

        # Pawns
        for p in pp:
            x = cellsizex / 2 + p.position[0]*cellsizex
            y = cellsizey / 2 + p.position[1]*cellsizey
            if y>=self.boardw_hei or x>=self.boardw_wid: continue
            scr.addch(y, x, ord(p.symbol), curses.color_pair(3) )

        # Barriers
        for b in barriers:
            p=b.node(0)
            x = p[0]*cellsizex
            y = p[1]*cellsizey
            if b.direction == right:
                if y>=self.boardw_hei: continue
                for i in range(1,b.length*cellsizex):
                    x += 1
                    if x>=self.boardw_wid: break
                    scr.addch(y, x,ord('X'), curses.color_pair(2) | curses.A_REVERSE )
            else:
                if x>=self.boardw_wid: continue
                for i in range(1,b.length*cellsizey):
                    y += 1
                    if y>=self.boardw_hei: break
                    scr.addch(y, x, ord('X'), curses.color_pair(2) | curses.A_REVERSE )

        # Arrows
#        for x in range(self.side):
#            for y in range(self.side):
#                if self.serverboard.moves[x][y] & up:
#                    xa = cellsizex / 2 + x*cellsizex
#                    ya = cellsizey / 2 + y*cellsizey - 1
#                    scr.addstr(oy+ya,ox+xa,'^', curses.color_pair(1) | curses.A_REVERSE )
#                if self.serverboard.moves[x][y] & right:
#                    xa = cellsizex / 2 + x*cellsizex + 1
#                    ya = cellsizey / 2 + y*cellsizey
#                    scr.addstr(oy+ya,ox+xa,'>', curses.color_pair(1) | curses.A_REVERSE )
#                if self.serverboard.moves[x][y] & down:
#                    xa = cellsizex / 2 + x*cellsizex
#                    ya = cellsizey / 2 + y*cellsizey + 1
#                    scr.addstr(oy+ya,ox+xa,'v', curses.color_pair(1) | curses.A_REVERSE )
#                if self.serverboard.moves[x][y] & left:
#                    xa = cellsizex / 2 + x*cellsizex - 1
#                    ya = cellsizey / 2 + y*cellsizey
#                    scr.addstr(oy+ya,ox+xa,'<', curses.color_pair(1) | curses.A_REVERSE )

        # Do the drawing
        scr.refresh()

    def draw_barrier_cursor(self,x,y):
        """Draw the cursor to select the barrier position."""

        if hasattr(self,'oldc') and hasattr(self,'oldp'):
            xc = self.oldp[0] * self.cellsizex
            yc = self.oldp[1] * self.cellsizey
            if xc<self.boardw_wid and yc<self.boardw_hei:
                self.board_win.addch(yc, xc, self.oldc & 255, self.oldc ^ (self.oldc & 255) )

        self.oldp = [x,y]
        xc = x * self.cellsizex
        yc = y * self.cellsizey
        self.oldc = self.board_win.inch(yc,xc)
        if xc<self.boardw_wid and yc<self.boardw_hei:
            self.board_win.addch(yc,xc,ord('X'), curses.color_pair(4) | curses.A_REVERSE )
        self.board_win.refresh()

    def delete_old_barrier_cursor(self):
        """Delete the old cursor to select the barrier position."""
        if hasattr(self,'oldc') and hasattr(self,'oldp'):
            xc = self.oldp[0] * self.cellsizex
            yc = self.oldp[1] * self.cellsizey
            if xc<self.boardw_wid and yc<self.boardw_hei:
                self.board_win.addch(yc, xc, self.oldc & 255, self.oldc ^ (self.oldc & 255) )
            del self.oldp
            del self.oldc

    def draw_barrier(self,x,y,d,l):
        """Draw a barrier."""

        if hasattr(self,'oldbp') and hasattr(self,'oldbd') and hasattr(self,'oldbc') and hasattr(self,'oldbl'):
            xc = self.oldbp[0] * self.cellsizex
            yc = self.oldbp[1] * self.cellsizey
            if self.oldbd == right:
                for i in range(1,self.oldbl*self.cellsizex):
                    xc += 1
                    occ = self.oldbc.pop(0)
                    if xc<self.boardw_wid and yc<self.boardw_hei:
                        self.board_win.addch(yc,xc, occ & 255 , occ ^ (occ & 255) )
            elif self.oldbd == down:
                for i in range(1,self.oldbl*self.cellsizey):
                    yc += 1
                    occ = self.oldbc.pop(0)
                    if xc<self.boardw_wid and yc<self.boardw_hei:
                        self.board_win.addch(yc,xc, occ & 255 , occ ^ (occ & 255) )
            elif self.oldbd == left:
                for i in range(1,self.oldbl*self.cellsizex):
                    xc -= 1
                    occ = self.oldbc.pop(0)
                    if xc<self.boardw_wid and yc<self.boardw_hei:
                        self.board_win.addch(yc,xc, occ & 255 , occ ^ (occ & 255) )
            elif self.oldbd == up:
                for i in range(1,self.oldbl*self.cellsizey):
                    yc -= 1
                    occ = self.oldbc.pop(0)
                    if xc<self.boardw_wid and yc<self.boardw_hei:
                        self.board_win.addch(yc,xc, occ & 255 , occ ^ (occ & 255) )

        self.oldbp = [x,y]
        self.oldbc = []
        self.oldbd = d
        self.oldbl = l
        xc = x * self.cellsizex
        yc = y * self.cellsizey
        if d == right:
            for i in range(1,l*self.cellsizex):
                xc += 1
                self.oldbc.append(self.board_win.inch(yc,xc))
                if xc<self.boardw_wid and yc<self.boardw_hei:
                    self.board_win.addch(yc,xc,ord('X'), curses.color_pair(4) | curses.A_REVERSE )
        elif d == down:
            for i in range(1,l*self.cellsizey):
                yc += 1
                self.oldbc.append(self.board_win.inch(yc,xc))
                if xc<self.boardw_wid and yc<self.boardw_hei:
                    self.board_win.addch(yc,xc,ord('X'), curses.color_pair(4) | curses.A_REVERSE )
        elif d == left:
            for i in range(1,l*self.cellsizex):
                xc -= 1
                self.oldbc.append(self.board_win.inch(yc,xc))
                if xc<self.boardw_wid and yc<self.boardw_hei:
                    self.board_win.addch(yc,xc,ord('X'), curses.color_pair(4) | curses.A_REVERSE )
        elif d== up:
            for i in range(1,l*self.cellsizey):
                yc -= 1
                self.oldbc.append(self.board_win.inch(yc,xc))
                if xc<self.boardw_wid and yc<self.boardw_hei:
                    self.board_win.addch(yc,xc,ord('X'), curses.color_pair(4) | curses.A_REVERSE )
        self.board_win.refresh()

    def delete_old_barrier(self):
        """Delete the old barrier."""
        if hasattr(self,'oldbp') and hasattr(self,'oldbd') and hasattr(self,'oldbc') and hasattr(self,'oldbl'):
            xc = self.oldbp[0] * self.cellsizex
            yc = self.oldbp[1] * self.cellsizey
            if self.oldbd == right:
                for i in range(1,self.oldbl*self.cellsizex):
                    xc += 1
                    occ = self.oldbc.pop(0)
                    if xc<self.boardw_wid and yc<self.boardw_hei:
                        self.board_win.addch(yc,xc, occ & 255 , occ ^ (occ & 255) )
            elif self.oldbd == down:
                for i in range(1,self.oldbl*self.cellsizey):
                    yc += 1
                    occ = self.oldbc.pop(0)
                    if xc<self.boardw_wid and yc<self.boardw_hei:
                        self.board_win.addch(yc,xc, occ & 255 , occ ^ (occ & 255) )
            elif self.oldbd == left:
                for i in range(1,self.oldbl*self.cellsizex):
                    xc -= 1
                    occ = self.oldbc.pop(0)
                    if xc<self.boardw_wid and yc<self.boardw_hei:
                        self.board_win.addch(yc,xc, occ & 255 , occ ^ (occ & 255) )
            elif self.oldbd == up:
                for i in range(1,self.oldbl*self.cellsizey):
                    yc -= 1
                    occ = self.oldbc.pop(0)
                    if xc<self.boardw_wid and yc<self.boardw_hei:
                        self.board_win.addch(yc,xc, occ & 255 , occ ^ (occ & 255) )

            del self.oldbp
            del self.oldbc
            del self.oldbl
            del self.oldbd

    def warn(self):
        curses.flash()

    def get_input(self):
        """Get input from the user."""
        return self.scr.getch()

    def draw_panel(self):
        pass

    def print_board_ascii(self):
        """Pretty-print the board in ASCII.
        
        Not used for the moment."""
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


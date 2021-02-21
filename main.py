import pygame as pg
import sys
# from pygame.locals import *
import pathlib
import math
import itertools
import tkinter as tki
from tkinter import filedialog

homedir = str(pathlib.Path(__file__).parent.absolute())
WHITE = "#F1F7ED"
BLACK = "#9B9B97"
FOCUS = "#97EDD3"
MOUSEOVER = "#0E9594"
BLACKCOVER = "#FF0000"
WHITECOVER = "#FFFFFF"
BOTHCOVER = "#888888"


class Main:
    def __init__(self, screensize):
        
        pg.init()
        self.clock = pg.time.Clock()
        
        self.osquare = None
        self.pickedPiece = None
        self.dragMode = False
        
        self.movecounter = 0
        self.legalMovelist = {}
        self.legalMoves = []
        self.activeColor = "w"
        self.swtichColor = {
            "w": "b",
            "b": "w"
        }
        self.rulebook = Rules(self)
        # self.board = Board(screensize[1])
        self.white = Player("w")
        self.black = Player("b")
        self.white.enemy = self.black
        self.black.enemy = self.white
        self.borw = {
            "w": self.white,
            "b": self.black
        }
        self.memory = Memory(self)
        self.initGame()
        self.updateLegalMovelist()
        self.ui = UI(self, screensize)

    def initGame(self):
        fen = "RNBQKBNR/PPPPPPPP/8/8/8/8/pppppppp/rnbqkbnr w KQkq - 0 0"
        self.memory.FENToState(fen)
        self.memory.writeToMemory(self.movecounter)

    def setFocus(self, square, toggleOn):
        if toggleOn:
            self.osquare = square
            self.pickedPiece = square.occupiedBy
            self.legalMoves = self.legalMovelist[self.osquare.id]
            self.osquare.focus = True
        else:
            self.osquare.focus = False
            self.osquare = None
            self.pickedPiece = None
            self.legalMoves = []

    def movePiece(self,square,toggleOn):
        if toggleOn:
            square.occupiedBy = None
            self.dragMode = True
        else:
            square.occupiedBy = self.pickedPiece
            self.dragMode = False

    def mouseGameControlsDown(self, xy):
        col = self.ui.maplist[math.floor(xy[0]/self.ui.squaresize)]
        row = self.ui.maplist[7-math.floor(xy[1]/self.ui.squaresize)]
        coords = (col,row)
        tsquare = self.memory.board[coords]
        # if square is not in legal moves: unfocus
        if tsquare.occupiedBy and tsquare.occupiedBy.color == self.activeColor:
            # 0. set focus
            if self.osquare:
                self.setFocus(self.osquare,False)
            self.setFocus(tsquare,True)
            # 3. set mode to dragging
            self.movePiece(tsquare,True)

        elif self.osquare:
            if coords in self.legalMoves:
                self.checkSpecialRules(coords)
                self.movePiece(self.osquare, True)
                self.movePiece(tsquare, False)
                self.setFocus(self.osquare,False)
                self.prepareNextMove()
            
            else:
                self.setFocus(self.osquare, False)

    def mouseGameControlsUp(self, xy):
        col = self.ui.maplist[math.floor(xy[0]/self.ui.squaresize)]
        row = self.ui.maplist[7-math.floor(xy[1]/self.ui.squaresize)]
        coords = (col, row)
        tsquare = self.memory.board[coords]

        if self.dragMode:
            if coords in self.legalMoves:
                self.checkSpecialRules(coords)
                self.movePiece(tsquare, False)
                self.prepareNextMove()
            else:
                self.movePiece(self.osquare, False)   

    def mouseSidebarControls(self,xy):
        x = xy[0] - self.ui.screensize[1]
        y = xy[1]

        # checking if a button is clicked:
        if self.ui.loadBtn.x <= x <= self.ui.loadBtn.dx and self.ui.loadBtn.y <= y <= self.ui.loadBtn.dy:
            self.memory.loadGame()
        elif self.ui.bwBtn.x <= x <= self.ui.bwBtn.dx and self.ui.bwBtn.y <= y <= self.ui.bwBtn.dy:
            self.memory.readFromMemory(self.movecounter-1)
        elif self.ui.fwBtn.x <= x <= self.ui.fwBtn.dx and self.ui.fwBtn.y <= y <= self.ui.fwBtn.dy:
            self.memory.readFromMemory(self.movecounter+1)
        elif self.ui.saveBtn.x <= x <= self.ui.saveBtn.dx and self.ui.saveBtn.y <= y <= self.ui.saveBtn.dy:
            self.memory.saveGame()

    def checkSpecialRules(self,coords):

        # checking castle rules
        castle = self.borw[self.activeColor].castle
        if castle["q"] or castle["k"]:
            if self.pickedPiece.type == "k":
                if coords == (6,0) and castle["k"]:
                    self.memory.board[(5, 0)].occupiedBy = self.white.initPieces["r"]
                    self.memory.board[(7, 0)].occupiedBy = None
                elif coords == (2,0) and castle["q"]:
                    self.memory.board[(3, 0)].occupiedBy = self.white.initPieces["r"]
                    self.memory.board[(0, 0)].occupiedBy = None

                elif coords == (6,7) and castle["k"]:
                    self.memory.board[(5, 7)].occupiedBy = self.black.initPieces["r"]
                    self.memory.board[(7, 7)].occupiedBy = None
                elif coords == (2,7) and castle["q"]:
                    self.memory.board[(3, 7)].occupiedBy = self.black.initPieces["r"]
                    self.memory.board[(0, 7)].occupiedBy = None
                castle["q"] = False
                castle["k"] = False


            elif self.pickedPiece.type == "r":
                if self.activeColor == "w":
                    if self.osquare.id == (0,0):
                        castle["q"] = False
                    elif self.osquare.id == (7,0):
                        castle["k"] = False
                if self.activeColor == "b":
                    if self.osquare.id == (0, 7):
                        castle["q"] = False
                    elif self.osquare.id == (7, 7):
                        castle["k"] = False
            
        #checking Promotion

        if self.pickedPiece.type == "p" and coords[1] == 7:
            self.pickedPiece = self.white.initPieces["q"]
        elif self.pickedPiece.type == "p" and coords[1] == 0:
            self.pickedPiece = self.black.initPieces["q"]
        
        #checking enpassant

        if self.pickedPiece.type == "p" and coords == self.memory.enpassant:
            if coords[1] == 2:
                self.memory.board[(coords[0], 3)].occupiedBy = None
            elif coords[1] == 5:
                self.memory.board[(coords[0], 4)].occupiedBy = None

        if self.pickedPiece.type == "p" and coords[1] == 3 and self.osquare.id[1] == 1:
            self.memory.enpassant = (coords[0],2)
        elif self.pickedPiece.type == "p" and coords[1] == 4 and self.osquare.id[1] == 6:
            self.memory.enpassant = (coords[0], 5)
        else:
            self.memory.enpassant = None

        #checking fiftyrule

        if self.pickedPiece.type == "p" or self.memory.board[coords].occupiedBy:
            self.memory.fiftyrule = 0
        else:
            self.memory.fiftyrule += 1
                             
    def prepareNextMove(self):
        self.pickedPiece = None
        self.legalMoves = []
        self.updateLegalMovelist()
        self.osquare = None
        self.activeColor = self.swtichColor[self.activeColor]
        self.movecounter += 1
        self.memory.writeToMemory(self.movecounter)
    
    def updateLegalMovelist(self):
        self.white.check = False
        self.black.check = False
        for key, square in self.memory.board.items():
            square.covered["b"] = False
            square.covered["w"] = False
                    
        for key, square in self.memory.board.items():
                coverlist = self.rulebook.getMoves( square, "cover")
                if square.occupiedBy:
                    color = square.occupiedBy.color
                    for squareID in coverlist:
                        self.memory.board[squareID].covered[color] = True
                        if self.memory.board[squareID].occupiedBy == self.borw[self.swtichColor[color]].initPieces["k"]:
                            self.borw[self.swtichColor[color]].check = True
                            print("check!")

        for key, square in self.memory.board.items():
            self.legalMovelist[key] = self.rulebook.getMoves(
                    square,"moves")

    def mainloop(self):
        while True:
            if self.dragMode and any([x > self.ui.boardsize-6 for x in pg.mouse.get_pos()]):
                self.movePiece(self.osquare,False)
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    pg.quit()
                    sys.exit()
                if event.type == pg.KEYDOWN:
                    if event.key == pg.K_SPACE:
                        self.ui.flip()
                    elif event.key == pg.K_RIGHT:
                        self.memory.readFromMemory(self.movecounter+1)
                    elif event.key == pg.K_LEFT:
                        self.memory.readFromMemory(self.movecounter-1)
                    elif pg.key.name(event.key) == "r":
                        self.memory.gameID = input("New GameID: ")
                    elif pg.key.name(event.key) == "c":
                        self.ui.displaycover = not self.ui.displaycover

                elif event.type == pg.MOUSEBUTTONDOWN:
                    if all(0 < x < self.ui.boardsize-5 for x in event.pos):
                            self.mouseGameControlsDown(event.pos)
        
                    elif (self.ui.boardsize < event.pos[0] < self.ui.screensize[0]):
                        self.mouseSidebarControls(event.pos)
                
                elif event.type == pg.MOUSEBUTTONUP:
                    if all(0 < x < self.ui.boardsize-5 for x in event.pos):
                            self.mouseGameControlsUp(event.pos)

            self.ui.update()
            self.clock.tick(30)

class Rules:
    def __init__(self,brain):
        self.brain = brain

    def getMoves(self,square,mode):

        def tadd(t1, t2):
            if len(t1) != len(t2):
                return None
            ans = ()
            for i in range(len(t1)):
                ans += (t1[i]+t2[i],)
            return ans


        movelist = []
        origin = square.id
        squares = self.brain.memory.board
        piece = square.occupiedBy

        if not piece:
            return movelist
        
        enemy = self.brain.swtichColor[piece.color]

        if piece.type == "p":
            #normal move
            heading = -1 + ord(piece.color)%2*2

            if mode != "cover":
                P_DIR = [(0, heading)]
                if (origin[1] == 1 and piece.color == "w") or (origin[1] == 6 and piece.color == "b"):
                    P_DIR.append((0, heading*2))

                for direction in P_DIR:
                    index = tadd(origin, direction)
                    if (0 <= index[0] <= 7) and (0 <= index[1] <= 7):
                        currentsquare = squares[index]
                        if not currentsquare.occupiedBy:
                            #case: free
                            movelist.append(index)
                        elif currentsquare.occupiedBy.color == enemy:
                            #case: enemy
                            break
                        else:
                            #case: own piece
                            break
            
            #take a piece or enpassant
            P_DIR = [(1, heading), (-1, heading)]
            for direction in P_DIR:
                index = tadd(origin, direction)
                if (0 <= index[0] <= 7) and (0 <= index[1] <= 7):
                    currentsquare = squares[index]
                    if index == self.brain.memory.enpassant:
                        movelist.append(index)
                    elif not currentsquare.occupiedBy:
                        pass
                    elif currentsquare.occupiedBy.color == enemy:
                        movelist.append(index)
                    elif mode == "cover" and currentsquare.occupiedBy.color == piece.color:
                        movelist.append(index)
                    


        elif piece.type == "k":
            K_DIR = [(1, 1), (-1, 1), (1, -1), (-1, -1),
                    (1, 0), (-1, 0), (0, 1), (0, -1)]

            for direction in K_DIR:

                index = tadd(origin, direction)
                if (0 <= index[0] <= 7) and (0 <= index[1] <= 7):
                    currentsquare = squares[index]
                    if currentsquare.covered[enemy]:
                        pass
                        #case: square is covered by enemy
                    elif not currentsquare.occupiedBy:
                        #case: free
                        movelist.append(index)
                    elif currentsquare.occupiedBy.color == enemy:
                        #case: enemy
                        movelist.append(index)
                    elif mode == "cover" and currentsquare.occupiedBy.color == piece.color:
                        movelist.append(index)
            
            if not squares[origin].covered[enemy]:
                if self.brain.borw[piece.color].castle["q"]:
                    if all([squares[column, origin[1]].occupiedBy == None and not squares[column, origin[1]].covered[enemy] for column in (1, 2, 3)]):
                        movelist.append((2,origin[1]))

                if self.brain.borw[piece.color].castle["k"]:
                    if all([squares[column, origin[1]].occupiedBy == None and not squares[column, origin[1]].covered[enemy] for column in (5, 6)]):
                        movelist.append((6, origin[1]))

        elif piece.type == "n":
            N_DIR = [(2, 1), (2, -1), (-2, 1), (-2, -1),
                    (1, 2), (1, -2), (-1, 2), (-1, -2)]

            for direction in N_DIR:

                index = tadd(origin, direction)
                if (0 <= index[0] <= 7) and (0 <= index[1] <= 7):
                    currentsquare = squares[index]
                    if not currentsquare.occupiedBy:
                        #case: free
                        movelist.append(index)
                    elif currentsquare.occupiedBy.color == enemy:
                        #case: enemy
                        movelist.append(index)
                    elif mode == "cover" and currentsquare.occupiedBy.color == piece.color:
                        movelist.append(index)

        elif piece.type == "r":
            R_DIR = [(1, 0), (-1, 0), (0, 1), (0, -1)]
            for direction in R_DIR:

                index = tadd(origin, direction)

                while (0 <= index[0] <= 7) and (0 <= index[1] <= 7):

                    currentsquare = squares[index]

                    if not currentsquare.occupiedBy:
                        #case: free
                        movelist.append(index)
                        index = tadd(index, direction)
                    elif currentsquare.occupiedBy.color == enemy:
                        #case: enemy
                        movelist.append(index)
                        break
                    elif mode == "cover" and currentsquare.occupiedBy.color == piece.color:
                        movelist.append(index)
                        break
                    else:
                        break

        elif piece.type == "b":
            B_DIR = [(1, 1), (-1, 1), (1, -1), (-1, -1)]
            for direction in B_DIR:

                index = tadd(origin, direction)

                while (0 <= index[0] <= 7) and (0 <= index[1] <= 7):

                    currentsquare = squares[index]

                    if not currentsquare.occupiedBy:
                        #case: free
                        movelist.append(index)
                        index = tadd(index, direction)
                    elif currentsquare.occupiedBy.color == enemy:
                        #case: enemy
                        movelist.append(index)
                        break
                    elif mode == "cover" and currentsquare.occupiedBy.color == piece.color:
                        movelist.append(index)
                        break
                    else:
                        #case: own piece
                        break


        elif piece.type == "q":
            Q_DIR = [(1, 1), (-1, 1), (1, -1), (-1, -1),
                    (1, 0), (-1, 0), (0, 1), (0, -1)]
            for direction in Q_DIR:

                index = tadd(origin, direction)

                while (0 <= index[0] <= 7) and (0 <= index[1] <= 7):

                    currentsquare = squares[index]

                    if not currentsquare.occupiedBy:
                        #case: free
                        movelist.append(index)
                        index = tadd(index, direction)
                    elif currentsquare.occupiedBy.color == enemy:
                        #case: enemy
                        movelist.append(index)
                        break
                    elif mode == "cover" and currentsquare.occupiedBy.color == piece.color:
                        movelist.append(index)
                        break
                    else:
                        #case: own piece
                        break

        return movelist

class UI:
    def __init__(self,brain,window_size):
        self.brain = brain
        self.screensize = window_size
        self.displaycover = False

        pg.font.init()
        self.myfont = pg.font.SysFont('Arial', 20)



        pg.display.set_caption("OpenChess")
        self.screen = pg.display.set_mode(self.screensize, 0, 32)
        self.initBoardUI()
        self.initSidebar()
        self.initImages()

    def initBoardUI(self):
        self.indexsize = 50
        self.boardsize = min(self.screensize)-self.indexsize
        self.maplist = list(range(8))
        self.COLORDICT = {
            True: WHITE,
            False: BLACK
        }
        self.squaresize = math.floor((self.boardsize)/8)
        self.squarecoords = {}
        for i in range(8):
            for j in range(8):
                self.squarecoords[i,j] = (i*self.squaresize,(7-j)*self.squaresize)
        
        self.rowindex = []
        self.colindex = []
        for i in range(8):
            self.colindex.append(
                ((i+.5)*self.squaresize, 8*self.squaresize+.5*self.indexsize))
            self.rowindex.append(
                (8*self.squaresize+.5*self.indexsize, (7.5-i)*self.squaresize))
        
    def initSidebar(self):
        self.sidebarwidth = self.screensize[0]-self.screensize[1]
        self.btnsize = 50
        self.padding = math.floor((self.sidebarwidth-4*self.btnsize)/(4+1))

        saveIcon = pg.image.load(homedir+f"/images/save-icon.png")
        saveIcon = pg.transform.scale(
            saveIcon, (self.btnsize, self.btnsize))
        loadIcon = pg.image.load(homedir+f"/images/load-icon.png")
        loadIcon = pg.transform.scale(
            loadIcon, (self.btnsize, self.btnsize))
        fwIcon = pg.image.load(homedir+f"/images/fw-icon.png")
        fwIcon = pg.transform.scale(
            fwIcon, (self.btnsize, self.btnsize))
        bwIcon = pg.image.load(homedir+f"/images/bw-icon.png")
        bwIcon = pg.transform.scale(
            bwIcon, (self.btnsize, self.btnsize))

        self.loadBtn = Button(self.padding,self.padding,self.btnsize,self.btnsize,loadIcon)
        self.bwBtn = Button(2*self.padding+self.btnsize, self.padding, self.btnsize, self.btnsize, bwIcon)
        self.fwBtn = Button(3*self.padding+2*self.btnsize, self.padding, self.btnsize, self.btnsize, fwIcon)
        self.saveBtn = Button(4*self.padding+3*self.btnsize, self.padding, self.btnsize, self.btnsize,saveIcon)

        self.buttonlist = [self.loadBtn, self.bwBtn,self.fwBtn,self.saveBtn]

    def initImages(self):

        self.images = {}
        for piece in itertools.product(("b", "w"), ("k", "q", "r", "n", "b", "p")):
            name = "".join(piece)
            image = pg.image.load(homedir+f"/images/{name}.png")
            image = pg.transform.scale(
                image, (self.squaresize, self.squaresize))
            self.images[name] = image
        

        moveicon = pg.image.load(homedir+f"/images/moveicon.png")
        self.images["moveicon"] = pg.transform.scale(
            moveicon, (self.squaresize, self.squaresize))
        moveiconHL = pg.image.load(homedir+f"/images/moveiconHL.png")
        self.images["moveiconHL"] = pg.transform.scale(
            moveiconHL, (self.squaresize, self.squaresize))
        

    def drawBoard(self):
        board = self.brain.memory.board
        pg.draw.rect(self.screen, BLACK, (0, 0)+self.screensize)

        for key, square in board.items():
            # color = square.color
            color = self.COLORDICT[(key[0]+key[1])%2==1]

            if square.covered["w"] and square.covered["b"] and self.displaycover:
                # print(key)
                color = BOTHCOVER
            elif square.covered["w"] and self.displaycover:
                # print("white ",key)
                color = WHITECOVER
            elif square.covered["b"] and self.displaycover:
                # print("black", key)
                color = BLACKCOVER    
            if square.focus:
                color = FOCUS
                
            pg.draw.rect(self.screen, color, pg.Rect(
                self.squarecoords[key], (self.squaresize, self.squaresize)))
            if square.occupiedBy:
                self.screen.blit(self.images[square.occupiedBy.imagecode], self.squarecoords[key])

        for i in range(8):
            text = self.myfont.render(chr(97+i), False, WHITE)
            self.screen.blit(text, text.get_rect(center=(self.colindex[i])))

            text = self.myfont.render(str(i+1), False, WHITE)
            self.screen.blit(text, text.get_rect(center=(self.rowindex[i])))
    
    def flip(self):
        self.colindex.reverse()
        self.rowindex.reverse()
        self.maplist.reverse()
        for row in range(8):
            for index in range(4):
                x1 = self.maplist[index]
                x2 = self.maplist[-index-1]

                self.squarecoords[(x1, row)], self.squarecoords[(x2, row)] = self.squarecoords[(
                    x2, row)], self.squarecoords[(x1, row)]

        for col in range(8):
            for index in range(4):
                y1 = self.maplist[index]
                y2 = self.maplist[-index-1]

                self.squarecoords[(col, y1)], self.squarecoords[(col, y2)] = self.squarecoords[(
                    col, y2)], self.squarecoords[(col, y1)]

    def drawDynamicPieces(self): 
        if self.brain.pickedPiece and self.brain.dragMode:
            image = self.images[self.brain.pickedPiece.imagecode]
            self.screen.blit(image, image.get_rect(
                center=pg.mouse.get_pos()))

    
    def drawLegalMoves(self):
        for index in self.brain.legalMoves:
            x = self.squarecoords[index][0]
            y = self.squarecoords[index][1]
            
            moveicon = self.images["moveicon"]
            mousex,mousey = pg.mouse.get_pos()

            colcoords = self.maplist[index[0]]*self.squaresize
            rowcoords = (7 - self.maplist[index[1]])*self.squaresize

            if 0 < mousex-colcoords< self.squaresize and 0 < mousey-rowcoords < self.squaresize:
                moveicon = self.images["moveiconHL"]

            self.screen.blit(moveicon,(x,y))
    
    def drawSidebar(self):
        for btn in self.buttonlist:
            self.screen.blit(btn.image,(self.screensize[1]+btn.x,btn.y))

    def update(self):
        self.drawBoard()
        self.drawLegalMoves()
        self.drawDynamicPieces()
        self.drawSidebar()

        pg.display.update()

class Memory:
    def __init__(self,brain):
        self.brain = brain
        self.initBoard()
        self.movelist = []
        self.gameID = "newGame.txt"
        self.enpassant = []
        self.fiftyrule = 0

    def initBoard(self):
        self.board = {}
        for i in range(8):
            for j in range(8):
                self.board[(j, i)] = Square(
                    (j, i), (None,None), None)
    
    def browseFiles(self, mode):
        root = tki.Tk()
        root.withdraw()  # use to hide tkinter window
        
        modedict = {
            "save": filedialog.asksaveasfilename,
            "load": filedialog.askopenfilename
        }

        filename = modedict[mode](initialdir=homedir+"/saves/",
                                  initialfile=self.gameID,
                                  title="Select a File",
                                        filetypes=(("Text files", "*.txt*"), ("all files", "*.*")))
        root.destroy()
        return filename

    def loadGame(self):
        filename = self.browseFiles("load")
        try:
            with open(filename, "r") as file:
                textsave = file.read()
        except FileNotFoundError:
            print("that game file does not exist.")
        else:
            self.movelist = textsave.split("\n")
            self.readFromMemory(len(self.movelist)-1)
            self.gameID = filename.split("/")[-1]
            print(self.gameID)


    def saveGame(self):
        filename = self.browseFiles("save")
        try:
            with open(filename,"w") as file:
                gamesave = "\n".join(self.movelist)
                file.write(gamesave)
        except FileNotFoundError:
            print("Invalid path.")
        else:
            self.gameID = filename.split("/")[-1]
            print(f"Game saved as {self.gameID}")
    
    def writeToMemory(self,index):
        # turn State into fen
        fen = self.StateToFEN()
        print(fen)
        # save fen into memory
        if index == 0:
            self.movelist = []
        elif index < len(self.movelist):
            self.movelist = self.movelist[:index]
        self.movelist.append(fen)

    def readFromMemory(self,index):
        if index < 0:
            index = 0
            return
        elif index > len(self.movelist)-1:
            index = len(self.movelist)-1
            return
        
        #read position from memory
        fen = self.movelist[index]

        # fen = "RNB1KBNR/PPPP1PPP/8/4P3/8/8/pppppppp/rnbqkbnr b 0-1"

        #convert into array

        self.FENToState(fen)
        if self.brain.osquare:
            self.brain.setFocus(None,False)
        self.brain.updateLegalMovelist()

    def StateToFEN(self):
        fen = ""

        spacecounter = 0
        for key, square in self.board.items():
            if not square.occupiedBy:
                spacecounter += 1
            else:
                if spacecounter > 0:
                    fen += str(spacecounter)
                    spacecounter = 0
                temp = square.occupiedBy.type
                if square.occupiedBy.color == "w":
                    temp = temp.upper()
                fen += temp

            if key[0] == 7 and key[1] != 7:
                if spacecounter > 0:
                    fen+= str(spacecounter)
                    spacecounter = 0
                fen += "/"

        
        castlepart = ""
        if self.brain.white.castle["k"]:
            castlepart += "K"
        if self.brain.white.castle["q"]:
            castlepart += "Q"
        if self.brain.black.castle["k"]:
            castlepart += "k"
        if self.brain.black.castle["q"]:
            castlepart += "q"

        if self.enpassant:
            enpassantpart = chr(97 + self.enpassant[0]) + str(self.enpassant[1]+1)
        else:
            enpassantpart = "-"

        fen += " " + self.brain.activeColor + " " + castlepart + " " + enpassantpart + " " + str(self.fiftyrule) + " " + str(self.brain.movecounter)

        return fen

    def FENToState(self,fen):
        blackPieces = self.brain.black.initPieces
        whitePieces = self.brain.white.initPieces
        for key,square in self.board.items():
            square.occupiedBy = None

        boardString, self.brain.activeColor, castlepart, enpassantpart, fiftyrule,  movecounter= fen.split(
            " ")

        self.brain.movecounter = int(movecounter)
        self.fiftyrule = int(fiftyrule)

        colindex,rowindex = 0,0

        for row in boardString.split("/"):
            colindex = 0
            for symbol in row:
                if symbol in ("k","q","r","n","b","p"):
                    self.board[(colindex,rowindex)].occupiedBy = blackPieces[symbol]

                elif symbol in ("K", "Q", "R", "N", "B", "P"):
                    self.board[(
                        colindex, rowindex)].occupiedBy = whitePieces[symbol.lower()]

                elif symbol in("1","2","3","4","5","6","7","8"):
                    colindex += int(symbol)-1

                colindex += 1
            rowindex += 1    

        for letter in castlepart:
            if letter == "K":
                self.brain.white.castle["k"] = True
            if letter == "Q":
                self.brain.white.castle["q"] = True
            if letter == "k":
                self.brain.black.castle["k"] = True
            if letter == "q":
                self.brain.black.castle["q"] = True
                
        if enpassantpart == "-":
            self.enpassant = None
        else:
            self.enpassant = (ord(enpassantpart[0])-97,int(enpassantpart[1])-1)

class Piece:
    def __init__(self,color,type):
        self.color = color
        self.type = type
        self.imagecode = f"{color}{type}"

class Player:
    def __init__(self,color):
        self.color = color
        self.enemy = None
        self.castle = {
            "k": True,
            "q": True
        }
        self.check = False
        self.initPieces = {}
        for piece in ("k", "q", "r", "n", "b", "p"):
            newpiece = Piece(color, piece)
            self.initPieces[piece] = newpiece

class Square:
    def __init__(self,xy,coords,color):
        self.id = xy
        self.coords = coords
        self.color = color
        self.occupiedBy = None
        self.focus = False
        self.covered = {
            "b" : False,
            "w" : False
        }

    def toggleFocus(self):
        global FOCUS
        if not self.focus:
            self.focus = True
        else:
            self.focus = False

class Button:
    def __init__(self, x,y,w,h,image):
        self.x = x
        self.y = y
        self.dx = x+w
        self.dy = y+h
        self.image = image

WINDOW_SIZE = (1200, 900)


chess = Main(WINDOW_SIZE)

chess.mainloop()







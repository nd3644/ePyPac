from sdl2 import *
import math
from enum import IntEnum
import json

class Direction(IntEnum):
    UP = 0
    DOWN = 1
    LEFT = 2
    RIGHT = 3

class Player:
    def __init__(self):
        self.PosX = 0
        self.PosY = 0
        self.CurrentDir = None
        self.UpdateTimer = SDL_GetTicks()

    def Draw(self):
        r = SDL_Rect(self.PosX + 8, self.PosY + 8, 8, 8)
        SDL_SetRenderDrawColor(myRenderer, 255, 255, 0, 255)
        SDL_RenderFillRect(myRenderer, r)

    def Update(self):

        if IsKeyDown(SDL_SCANCODE_A):
            indexX = round((self.PosX + 8) / 8)
            indexY = round((self.PosY + 8) / 8)
            if myMaze[indexY][indexX-1] == -1:
                if round(self.PosY / 8) * 8 == self.PosY:
                    self.CurrentDir = Direction.LEFT
        
        elif IsKeyDown(SDL_SCANCODE_D):
            indexX = round((self.PosX + 8) / 8)
            indexY = round((self.PosY + 8) / 8)
            if myMaze[indexY][indexX+1] == -1:
                if round(self.PosY / 8) * 8 == self.PosY:
                    self.CurrentDir = Direction.RIGHT

        if IsKeyDown(SDL_SCANCODE_W):
            indexX = round((self.PosX + 8) / 8)
            indexY = round((self.PosY + 8) / 8)
            if myMaze[indexY-1][indexX] == -1:
                if round(self.PosX / 8) * 8 == self.PosX:
                    self.CurrentDir = Direction.UP
        
        elif IsKeyDown(SDL_SCANCODE_S):
            indexX = round((self.PosX + 8) / 8)
            indexY = round((self.PosY + 8) / 8)
            if myMaze[indexY+1][indexX] == -1:
                if round(self.PosX / 8) * 8 == self.PosX:
                    self.CurrentDir = Direction.DOWN

        if(SDL_GetTicks() - self.UpdateTimer < 20):
            return

        self.UpdateTimer = SDL_GetTicks()
        moveDelta = [ 0, 0 ]
        if self.CurrentDir == Direction.LEFT:
            indexX = round((self.PosX + 11) / 8)
            indexY = round((self.PosY + 8) / 8)
            if myMaze[indexY][indexX-1] == -1:
                self.PosX -= 1
        
        elif self.CurrentDir == Direction.RIGHT:
            indexX = round((self.PosX + 4) / 8)
            indexY = round((self.PosY + 8) / 8)
            if myMaze[indexY][indexX+1] == -1:
                self.PosX += 1


        if self.CurrentDir == Direction.UP:
            indexX = round((self.PosX + 8) / 8)
            indexY = round((self.PosY + 11) / 8)
            if myMaze[indexY-1][indexX] == -1:
                self.PosY -= 1
        
        elif self.CurrentDir == Direction.DOWN:
            indexX = round((self.PosX + 8) / 8)
            indexY = round((self.PosY + 4) / 8)
            if myMaze[indexY+1][indexX] == -1:
                self.PosY += 1

        self.PosX += moveDelta[0]
        self.PosY += moveDelta[1]


# The game should be split into 3 states
# TITLE is just the title screen
# GAME is when the game is live and running
# EDIT is for editing the maze and pellets etc
class GameState(IntEnum):
        STATE_TITLE = 0
        STATE_GAME = 1
        STATE_EDIT = 2


myKeyStates = [False] * 255
myFormerKeyStates = [False] * 255
myGameState = GameState.STATE_TITLE
myPlayer = Player()

def PollKeyboard():
    keys = SDL_GetKeyboardState(None)
    for i in range(255):
        myFormerKeyStates[i] = myKeyStates[i]
        myKeyStates[i] = keys[i]

bPreviewShown = False
def DrawEditPreview():
    r = SDL_Rect(0,0,128,128)
    c = SDL_Rect(0,0,256,256)
#    SDL_RenderCopy(myRenderer, tilesTex, c, r)


EditCursorX = 0
EditCursorY = 0
def CheckInputs():
    global myGameState, EditCursorX, EditCursorY
    if myGameState == GameState.STATE_EDIT:
        if IsKeyTap(SDL_SCANCODE_A):
            EditCursorX -= 1

        if IsKeyTap(SDL_SCANCODE_D):
            EditCursorX += 1

        if IsKeyTap(SDL_SCANCODE_W):
            EditCursorY -= 1

        if IsKeyTap(SDL_SCANCODE_S):
            EditCursorY += 1

        if IsKeyTap(SDL_SCANCODE_8):
            SaveMaze()

        if IsKeyTap(SDL_SCANCODE_9):
            LoadMaze()

        delta = 1
        if IsKeyDown(SDL_SCANCODE_LCTRL):
            delta = 8

        if IsKeyTap(SDL_SCANCODE_E):
            myMaze[EditCursorY][EditCursorX] += delta

        if IsKeyTap(SDL_SCANCODE_Q):
            myMaze[EditCursorY][EditCursorX] -= delta


    if IsKeyTap(SDL_SCANCODE_3):
        myGameState = GameState.STATE_EDIT


def LoadMaze():
    global myMaze
    with open("maze", "r") as f:
        myMaze = json.load(f)

    print("loaded")

def SaveMaze():
    global myMaze
    with open("maze", "w") as f:
        json.dump(myMaze, f)

    print("saved...")
        

def IsKeyDown(which):
    return myKeyStates[which]

def IsKeyTap(which):
    return (myKeyStates[which] == True and myFormerKeyStates[which] == False)

SDL_Init(SDL_INIT_VIDEO)

myWindow = SDL_CreateWindow(b"HelloPy", SDL_WINDOWPOS_UNDEFINED, SDL_WINDOWPOS_UNDEFINED, 224*2, 248*2, SDL_WINDOW_SHOWN)
myWindowSurf = SDL_GetWindowSurface(myWindow)

myRenderer = SDL_CreateRenderer(myWindow, -1, SDL_RENDERER_ACCELERATED)
SDL_RenderSetScale(myRenderer, 2, 2)

SDL_GL_SetSwapInterval(1)

myEvent = SDL_Event()

smile = SDL_LoadBMP(b"logo.bmp")
if smile == None:
    print("couldn't load logo.bmp")
smileTex = SDL_CreateTextureFromSurface(myRenderer, smile)

tilesSurf = SDL_LoadBMP(b"tiles.bmp")
tilesTex = SDL_CreateTextureFromSurface(myRenderer, tilesSurf)

MazeWidth = 28
MazeHeight = 31
myMaze = [  [3,   4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4, 36, 35, 4,  4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 5],# 1
            [11, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 8,  10, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 13],# 2
            [11, -1,  0, 1,  1,  2,  -1,  0,  1,  1,  1, 2,  -1, 8,  10, -1, 0, 1, 1, 1, 2, -1,     0, 1, 1, 2, -1, 13],# 3
            [11, -1, 8, -1, -1, 10,  -1,  8, -1, -1, -1, 10, -1, 8,  10, -1, 8, -1, -1, -1, 10, -1, 8, -1,  -1, 10, -1, 13],# 4
            [11, -1, 16, 17, 17, 18, -1, 16, 17, 17, 17, 18, -1, 16, 18, -1, 16, 17, 17, 17, 18, -1, 16, 17, 17, 18, -1, 13],# 5
            [11, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 13],# 6
            [11, -1, 0, 1, 1, 2, -1, 0, 2, -1, 0, 1, 1, 1, 1, 1, 1, 2, -1, 0, 2, -1, 0, 1, 1, 2, -1, 13], # 7
            [11, -1, 16, 17, 17, 18, -1, 8, 10, -1, 16, 17, 17, 2, 0, 17, 17, 18, -1, 8, 10, -1, 16, 17, 17, 18, -1, 13], # 8
            [11, -1, -1, -1, -1, -1, -1, 8, 10, -1, -1, -1, -1, 8, 10, -1, -1, -1, -1, 8, 10, -1, -1, -1, -1, -1, -1, 13], # 9
            [19, 20, 20, 20, 20, 2, -1, 8, 14, 1, 1, 2, -1, 8, 10, -1,   0, 1, 1, 15, 10, -1, 0, 20, 20, 20, 20, 21], # 1-1
            [-1, -1, -1, -1, -1, 11, -1, 8, 0, 17, 17, 18, -1, 16, 18, -1, 16, 17, 17, 2, 10, -1, 13, -1, -1, -1, -1, -1], # 11
            [-1, -1, -1, -1, -1, 11, -1, 8, 10, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 8, 10, -1, 13, -1, -1, -1, -1, -1], # 12
            [-1, -1, -1, -1, -1, 11, -1, 8, 10, -1, 24, 25, 25, 12, 12, 25, 25, 26, -1, 8, 10, -1, 13, -1, -1, -1, -1, -1], # 13
            [4, 4, 4, 4, 4, 18, -1, 16, 18, -1, 32, -1, -1, -1, -1, -1, -1, 34, -1, 16, 18, -1, 16, 4, 4, 4, 4, 4], # 14
            [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 32, -1, -1, -1, -1, -1, -1, 34, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1], # 15
            [20, 20, 20, 20, 20, 2, -1, -1, -1, -1, 32, -1, -1, -1, -1, -1, -1, 34, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1], # 16
            [-1, -1, -1, -1, -1, 11, -1, -1, -1, -1, 40, 41, 41, 41, 41, 41, 41, 42, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1], # 17
            [-1, -1, -1, -1, -1, 11, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1], # 18
            [-1, -1, -1, -1, -1, 11, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1], # 19
            [3,  4,   4,  4,  4, 18, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1], # 2-1
            [11, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1], # 21
            [11, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1], # 22
            [11, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1], # 23
            [11, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1], # 24
            [16,  1, 2, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1], # 25
            [0, 1, 18, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1], # 26
            [11, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 13], # 27
            [11, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 13], # 28
            [11, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 13], # 29
            [11, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 13], # 3-1
            [19, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 21]] # 31

def DrawMaze():
    global myGameState
    for x in range(28):
        for y in range(31):
            tileID = myMaze[y][x]
            if tileID == -1:
                continue

            cropX = math.floor((tileID) % 8) * 8
            cropY = math.floor((tileID) / 8) * 8

            posX = x * 8
            posY = y * 8

            crop = SDL_Rect(int(cropX),int(cropY),8,8)
            rect = SDL_Rect(posX, posY, 8, 8)
            SDL_RenderCopy(myRenderer, tilesTex, crop, rect)

            SDL_SetRenderDrawColor(myRenderer, 0, 0, 255, 255)
            SDL_RenderDrawRect(myRenderer, rect)

    if myGameState == GameState.STATE_EDIT:
        posX = EditCursorX * 8
        posY = EditCursorY * 8
        r = SDL_Rect(posX, posY, 8, 8)

        SDL_SetRenderDrawColor(myRenderer, 0, 0, 255, 255)
        SDL_RenderDrawRect(myRenderer, r)
        DrawEditPreview()


LoadMaze()
done = False
while done == False:
    while SDL_PollEvent(myEvent):
        if myEvent.type == SDL_QUIT:
            done = True

    SDL_SetRenderDrawColor(myRenderer, 0, 0, 0, 255)
    SDL_RenderClear(myRenderer)

    PollKeyboard()
    CheckInputs()
    

    if myKeyStates[SDL_SCANCODE_ESCAPE] == True:
        done = True

    DrawMaze()
    
    myPlayer.Update()
    myPlayer.Draw()
    SDL_RenderPresent(myRenderer)
    

SDL_DestroyWindow(myWindow)
SDL_Quit()
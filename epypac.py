# Pac-man - Nicole Durrant 2020

from sdl2 import *
from sdl2.sdlmixer import *
from sdl2.sdlttf import *
import math
import random
from enum import IntEnum
import json
import ctypes

xScale = 2
yScale = 2
HUD_HEIGHT = 24

'''
Each round, the player is given four Scatter mode breaks. The first one begins
at the beginning of the round. After each Scatter mode, there is a 20-second
Attack mode for the ghosts. The first two Scatter modes are seven seconds long,
and the second two Scatter modes are five seconds long. After the last Scatter
mode, the ghosts will constantly attack until Pac-Man advances to the next
round or loses a life to a ghost.
'''

class Direction(IntEnum):
    UP = 0
    DOWN = 1
    LEFT = 2
    RIGHT = 3

def LoadTexture(filename):
    surf = SDL_LoadBMP(filename)
    if surf == None:
        print(f"couldn't load {filename}")
    SDL_SetColorKey(surf, SDL_TRUE, 0)
    tex = SDL_CreateTextureFromSurface(myRenderer, surf)
    SDL_FreeSurface(surf)
    return tex

def FlipDirection(r):
    newDir = None
    if r == Direction.LEFT:
        nerwDir = Direction.RIGHT
    elif r == Direction.RIGHT:
        r = Direction.LEFT
    elif r == Direction.UP:
        newDir = Direction.DOWN
    elif r == Direction.DOWN:
        newDir = Direction.UP

    return newDir

def CalcLinearDist(x1, y1, x2, y2):
    distX = x2 - x1
    distY = y2 - y1
    return math.sqrt((distX * distX) + (distY * distY))

def DirectionToVec(dir):
    vec = [ 0, 0 ]
    if dir == Direction.UP:
        vec = [ 0, -1 ]
    elif dir == Direction.DOWN:
        vec = [ 0, 1 ]
    elif dir == Direction.LEFT:
        vec = [ -1, 0 ]
    elif dir == Direction.RIGHT:
        vec = [ 1, 0 ]
    return vec

def Clamp(i, min, max):
    if i < min:
        i = min
    elif i > max:
        i = max
    return int(i)

def IndexArr(y, x):
    if x >= 28:
        return -1
    elif x < 0:
        return -1
    if y >= MazeHeight:
        return -1
    elif y < 0:
        return -1
    if y == 14 and x == 27:
        return -1
    return myMaze[y][x]


def CountFood():
    count = 0
    for i in range(0, MazeWidth):
        for j in range(0, MazeHeight):
            if arr[j][i] != 0:
                count += 1

    return count

# The game should be split into 3 states
# TITLE is just the title screen
# GAME is when the game is live and running
# EDIT is for editing the maze and pellets etc
class GameState(IntEnum):
        STATE_TITLE = 0
        STATE_STARTING = 1
        STATE_GAME = 2
        STATE_EDIT = 3

myGameState = GameState.STATE_TITLE
mySounds = { }
myKeyStates = [False] * 255
myFormerKeyStates = [False] * 255

class GhostState(IntEnum):
    STATE_SCATTER = 0
    STATE_CHASE = 1
    STATE_RESPAWNING = 2
    STATE_FRIGHTENED = 3
    STATE_INHOUSE = 4

class Ghost:
    def __init__(self):
        self.Reset()

    def Frighten(self):
        self.State = GhostState.STATE_FRIGHTENED
#        self.CurrentDir = FlipDirection(self.CurrentDir)

        self.Target[1] = 0
        self.Target[0] = 0

        self.FrightenTimer = SDL_GetTicks()

    def Reset(self):
        self.PosX = 0
        self.PosY = 0
        self.Name = "Spook"
        self.Texture = None
        self.EyesTex = None
        self.FrightenedTex = None
        self.Target = [ 5, 5 ]
#        self.ScatterTarget = [ 0, 0 ]
        self.NextTile = [ 1, 0 ]
        self.CurrentDir = Direction.RIGHT
        self.FormerDir = Direction.LEFT
        self.LastDir = Direction.RIGHT
        self.UpdateTimer = SDL_GetTicks()
        self.DbgMode = True
        self.MoveDelta = 0
        self.State = GhostState.STATE_SCATTER
        self.FrightenTimer = 0

    def TryDirChange(self, dir):
        # The way the ghosts change direction has become a little more complicated that it had to be.
        # The fence tile should be considered an exception when checking for adjacent walls,
        # but only when *leaving* the ghost house, otherwise we can consider an exception when the ghosts are dead
        # and returning to respawn
        px = self.PosX + 12
        py = self.PosY + 12
        # 12 is the exception for the ghost house- This needs fixing
        if dir == Direction.UP and myMaze[int((py-5) / 8)][int((px) / 8)] == -1 or myMaze[int((py-5) / 8)][int((px) / 8)] == 12:
            return True
        elif dir == Direction.DOWN and myMaze[int((py+5) / 8)][int((px) / 8)] == -1 or (myMaze[int((py+4) / 8)][int((px) / 8)] == 12 and self.State == GhostState.STATE_RESPAWNING):
            return True
        elif dir == Direction.LEFT and myMaze[int((py) / 8)][int((px-5) / 8)] == -1 or (myMaze[int((py) / 8)][int((px-4) / 8)] == 12 and self.State == GhostState.STATE_RESPAWNING):
            return True
        elif dir == Direction.RIGHT and myMaze[int((py) / 8)][int((px+4) / 8)] == -1 or (myMaze[int((py-5) / 8)][int((px+4) / 8)] == 12 and self.State == GhostState.STATE_RESPAWNING):
            return True
        return False

    def UpdateHouseTarget(self):
        px = self.PosX + 12
        py = self.PosY + 12
        if px > 90 and py > 105 and px < 135 and py < 125:
            self.Target[0] = 13
            self.Target[1] = 11


    def Update(self):
        if myGameState != GameState.STATE_GAME:
            return

        if self.State == GhostState.STATE_RESPAWNING:
            self.Target[0] = 13
            self.Target[1] = 14

            if round((self.PosX + 12) / 8) == self.Target[0] and round((self.PosY + 12) / 8) == self.Target[1]:
                self.State = GhostState.STATE_SCATTER


        #
        px = self.PosX + 12
        py = self.PosY + 12
        if IsKeyDown(SDL_SCANCODE_SPACE):
            if IsKeyTap(SDL_SCANCODE_A):
                self.State = GhostState.STATE_RESPAWNING
            if IsKeyTap(SDL_SCANCODE_D):
                self.State = GhostState.STATE_SCATTER
            if IsKeyTap(SDL_SCANCODE_W):
                self.State = GhostState.STATE_CHASE
            if IsKeyTap(SDL_SCANCODE_S):
                self.Target[1] += 1

        # 

        UpdateDelta = 15
        if self.State == GhostState.STATE_RESPAWNING:
            UpdateDelta = 10
            
        if SDL_GetTicks() - self.UpdateTimer < UpdateDelta:
            return

        self.UpdateTimer = SDL_GetTicks()
        if self.MoveDelta > 0:
            self.MoveDelta -= 1
            # Stuff to update on timeout
            if self.CurrentDir == Direction.RIGHT:
                self.PosX += 1
            elif self.CurrentDir == Direction.LEFT:
                self.PosX -= 1
            elif self.CurrentDir == Direction.UP:
                self.PosY -= 1
            elif self.CurrentDir == Direction.DOWN:
                self.PosY += 1
        else:
            if self.State == GhostState.STATE_FRIGHTENED:
                if SDL_GetTicks() - self.FrightenTimer > 1000 * 10:
                    self.State = GhostState.STATE_CHASE

#            if IsKeyTap(SDL_SCANCODE_RETURN):
            stringTrans = { Direction.LEFT: "left", Direction.RIGHT: "right", Direction.UP: "up", Direction.DOWN: "down" }
            self.MoveDelta = 8
                

            aboveDist = CalcLinearDist(px, py-1, self.Target[0] * 8, self.Target[1] * 8)
            belowDist = CalcLinearDist(px, py+1, self.Target[0] * 8, self.Target[1] * 8)
            leftDist = CalcLinearDist(px-1, py, self.Target[0] * 8, self.Target[1] * 8)
            rightDist = CalcLinearDist(px+1, py, self.Target[0] * 8, self.Target[1] * 8)

            Distances = { Direction.LEFT: leftDist, Direction.RIGHT: rightDist, Direction.UP: aboveDist, Direction.DOWN: belowDist }
            if self.CurrentDir == Direction.UP:
                Distances.pop(Direction.DOWN)
            elif self.CurrentDir == Direction.DOWN:
                Distances.pop(Direction.UP)
            elif self.CurrentDir == Direction.LEFT:
                Distances.pop(Direction.RIGHT)
            elif self.CurrentDir == Direction.RIGHT:
                Distances.pop(Direction.LEFT)
            #print(f"popping {stringTrans[self.FormerDir]}")

            DistancesCopy = Distances.copy()
            # remove directions that lead to walls
            i = 0
            for key in DistancesCopy:
                i += 1
                if self.TryDirChange(key) == False:
                    #print(f"can't go {stringTrans[key]}")
                    Distances.pop(key)



            priorityMap = { Direction.UP: 0, Direction.LEFT: 1, Direction.DOWN: 2, Direction.RIGHT: 3 }
            first = True
            lowestDist = 0
            lowestKey = Direction.UP
            for key in Distances:
                if Distances[key] < lowestDist or first == True:
                    lowestDist = Distances[key]
                    lowestKey = key
                    first = False
                elif Distances[key] == lowestDist: # if the distances are equal
                    # use the priority map to decide
                    if priorityMap[key] < priorityMap[lowestKey]:
                        lowestDist = Distances[key]
                        lowestKey = key


            
            #print(f"move should be: {stringTrans[lowestKey]}")
            self.CurrentDir = lowestKey
                
    def Draw(self):
        if myGameState == GameState.STATE_STARTING:
            return

        if self.Texture == None:
            self.Texture = LoadTexture(b"spook.bmp")

        if self.EyesTex == None:
            self.EyesTex = LoadTexture(b"eyes.bmp")

        if self.FrightenedTex == None:
            self.FrightenedTex = LoadTexture(b"fright.bmp")

        cropMap = { None: 0, Direction.UP: 0, Direction.DOWN: 16, Direction.LEFT: 32, Direction.RIGHT: 48 }
        c = SDL_Rect(0,cropMap[self.CurrentDir],16,16)
        r = SDL_Rect(self.PosX + 4, self.PosY + 4, 16,16)
        r.y += HUD_HEIGHT

        if self.State == GhostState.STATE_RESPAWNING:
            SDL_RenderCopy(myRenderer, self.EyesTex, c, r)
        elif self.State == GhostState.STATE_FRIGHTENED:
            c.x = c.y = 0
            if SDL_GetTicks() - self.FrightenTimer > 1000 * 7:
                c.y = random.randint(0, 1) * 16

            SDL_RenderCopy(myRenderer, self.FrightenedTex, c, r)
        else:
            SDL_RenderCopy(myRenderer, self.Texture, c, r)

        SDL_RenderDrawPoint(myRenderer, self.PosX + 12, self.PosY + 12 + HUD_HEIGHT)


        if self.DbgMode == True:
            SDL_SetRenderDrawColor(myRenderer, 0, 255, 0, 255)
            SDL_RenderDrawPoint(myRenderer, (self.Target[0] * 8) + 4, (self.Target[1] * 8) + 4 + HUD_HEIGHT)
            SDL_RenderDrawPoint(myRenderer, (self.Target[0] * 8) + 3, (self.Target[1] * 8) + 4 + HUD_HEIGHT)
            SDL_RenderDrawPoint(myRenderer, (self.Target[0] * 8) + 5, (self.Target[1] * 8) + 4 + HUD_HEIGHT)
            SDL_RenderDrawPoint(myRenderer, (self.Target[0] * 8) + 4, (self.Target[1] * 8) + 3 + HUD_HEIGHT)
            SDL_RenderDrawPoint(myRenderer, (self.Target[0] * 8) + 4, (self.Target[1] * 8) + 5 + HUD_HEIGHT)


class Blinky(Ghost):
    def __init__(self):
        super().__init__()

    def Reset(self):
        super().Reset()
        self.PosX = (13 * 8)
        self.PosY = 10 * 8

    def Draw(self):
        if self.Texture == None:
            self.Texture = LoadTexture(b"blinky.bmp")
        super().Draw()

    def Update(self):
        super().Update()

        if self.State == GhostState.STATE_CHASE:
            self.Target[0] = int((myPlayer.PosX + 8) / 8)
            self.Target[1] = int((myPlayer.PosY + 8) / 8)
        elif self.State == GhostState.STATE_SCATTER:
            self.Target[0] = 27
            self.Target[1] = 0

        self.UpdateHouseTarget()

class Pinky(Ghost):
    def __init__(self):
        super().__init__()
    
    def Reset(self):
        super().Reset()
        self.PosX = (13 * 8)
        self.PosY = 13 * 8

    def Draw(self):
        if self.Texture == None:
            self.Texture = LoadTexture(b"pinky.bmp")
        super().Draw()

    def Update(self):
        super().Update()

        if self.State == GhostState.STATE_CHASE:
            vec = DirectionToVec(myPlayer.CurrentDir)
            vec[0] *= 4
            vec[1] *= 4

            self.Target[0] = int((myPlayer.PosX + 8) / 8)
            self.Target[1] = int((myPlayer.PosY + 8) / 8)

            self.Target[0] += vec[0]
            self.Target[1] += vec[1]

        elif self.State == GhostState.STATE_SCATTER:
            self.Target[0] = 0
            self.Target[1] = 0

        self.UpdateHouseTarget()
class Inky(Ghost):
    def __init__(self):
        super().__init__()
        self.PosX = (11 * 8)
        self.PosY = 13 * 8
        
    def Draw(self):
        if self.Texture == None:
            self.Texture = LoadTexture(b"inky.bmp")
        super().Draw()

    def Update(self):
        super().Update()

        if self.State == GhostState.STATE_CHASE:
            
            # First, get the tile 2 ahead of pac-man
            vec = DirectionToVec(myPlayer.CurrentDir)
            vec[0] *= 4
            vec[1] *= 4

            self.Target[0] = int((myPlayer.PosX + 8) / 8)
            self.Target[1] = int((myPlayer.PosY + 8) / 8)

            self.Target[0] += vec[0]
            self.Target[1] += vec[1]

            # Get the distance between the target tile and Blinky
            distX = self.Target[0] - (myGhosts["blinky"].PosX / 8)
            distY = self.Target[0] - (myGhosts["blinky"].PosY / 8)

            self.Target[0] -= int(distX)
            self.Target[1] -= int(distY)


        elif self.State == GhostState.STATE_SCATTER:
            self.Target[0] = 27
            self.Target[1] = 30

        self.UpdateHouseTarget()

class Clyde(Ghost):
    def __init__(self):
        super().__init__()

    def Reset(self):
        super().Reset()
        self.PosX = (15 * 8)
        self.PosY = 13 * 8

    def Draw(self):
        if self.Texture == None:
            self.Texture = LoadTexture(b"clyde.bmp")
        super().Draw()

    def Update(self):
        super().Update()

        if self.State == GhostState.STATE_CHASE:
            vec = DirectionToVec(myPlayer.CurrentDir)
            vec[0] *= 4
            vec[1] *= 4

            self.Target[0] = int((myPlayer.PosX + 8) / 8)
            self.Target[1] = int((myPlayer.PosY + 8) / 8)

        elif self.State == GhostState.STATE_SCATTER:
            self.Target[0] = 0
            self.Target[1] = 30
        
        self.UpdateHouseTarget()

myGhosts = { "blinky": Blinky(), "inky": Inky(), "pinky": Pinky(), "clyde": Clyde() }

def ResetGame():
    myPlayer.Reset()
    for k in myGhosts:
        myGhosts[k].Reset()

    LoadMaze()

class Player:
    def __init__(self):
        self.Reset()

    def Reset(self):
        self.PosX = (13 * 8)-4
        self.PosY = 16 * 8
        self.CurrentDir = None
        self.UpdateTimer = SDL_GetTicks()
        self.AnimTimer = SDL_GetTicks()
        self.CurrentFrame = 0
        self.bMoving = False
        self.NumLives = 5

    def Draw(self):
        if myGameState == GameState.STATE_STARTING:
            return

        r = SDL_Rect(self.PosX + 4, self.PosY + 4, 16, 16)
        crop = SDL_Rect(0,0,16,16)
        cropMap = { None: 0, Direction.UP: 0, Direction.DOWN: 16, Direction.LEFT: 32, Direction.RIGHT: 48 }
        crop.x = self.CurrentFrame * 16
        crop.y = cropMap[self.CurrentDir]

        r.y += HUD_HEIGHT
        SDL_RenderCopy(myRenderer, playerTex, crop, r)

        if SDL_GetTicks() - self.AnimTimer < 60 or self.CurrentDir == None:
            return

        self.AnimTimer = SDL_GetTicks()
        if self.CurrentFrame == 2:
            self.CurrentFrame = 0
        else:
            self.CurrentFrame += 1

    def Update(self):
        global CurrentScore

        if myGameState != GameState.STATE_GAME:
            return
        # center positions for array indexing
        py = self.PosY + 12
        px = self.PosX + 12

        roundedX = (self.PosX == (round(self.PosX / 8) * 8))
        roundedY = (self.PosY == (round(self.PosY / 8) * 8))

    	# Update every frame here ...
        if IsKeyDown(SDL_SCANCODE_LEFT) and roundedY == True and myMaze[int((py) / 8)][Clamp(int((px-5) / 8), 0, MazeWidth-1)] == -1:
            self.CurrentDir = Direction.LEFT
        elif IsKeyDown(SDL_SCANCODE_RIGHT)  and roundedY == True and myMaze[int((py) / 8)][Clamp(int((px+4) / 8), 0, MazeWidth-1)] == -1:
            self.CurrentDir = Direction.RIGHT
        elif IsKeyDown(SDL_SCANCODE_UP) and roundedX == True and myMaze[int((py-5) / 8)][int((px) / 8)] == -1:
            self.CurrentDir = Direction.UP
        elif IsKeyDown(SDL_SCANCODE_DOWN) and roundedX == True and myMaze[int((py+4) / 8)][int((px) / 8)] == -1:
            self.CurrentDir = Direction.DOWN
        
        if(SDL_GetTicks() - self.UpdateTimer < 20):
            return
        self.UpdateTimer = SDL_GetTicks()

        # Update on timeout here ...
        self.bMoving = True
        a = Clamp(int((px+4) / 8), 0, MazeWidth-1)
        b = (px+4) / 8
#        print(f"{a}, {b}")
#        if self.CurrentDir == Direction.RIGHT and myMaze[int((py) / 8)][Clamp(int((px+4) / 8), 0, MazeWidth-1)] == -1:
        aa = int((px+4) / 8)
        bb = int(((py) / 8))
#        print(f"indexing: {aa}, {bb}")
        if self.CurrentDir == Direction.RIGHT and IndexArr(int((py) / 8), int((px+4) / 8)) == -1:
            self.PosX += 1
            if self.PosX / 8 > MazeWidth:
                self.PosX = -8
        elif self.CurrentDir == Direction.LEFT and myMaze[int((py) / 8)][Clamp(int((px-5) / 8), 0, MazeWidth-1)] == -1:
            self.PosX -= 1
            if self.PosX < -16:
                self.PosX = 208

        elif self.CurrentDir == Direction.UP and myMaze[int((py-5) / 8)][int((px) / 8)] == -1:
            self.PosY -= 1
        elif self.CurrentDir == Direction.DOWN and myMaze[int((py+4) / 8)][int((px) / 8)] == -1:
            self.PosY += 1
        else:
            self.bMoving = False

        global arr
        lx = Clamp(round((self.PosX + 8) / 8), 0, MazeWidth)
        ly = Clamp(round((self.PosY + 8) / 8), 0, MazeHeight)
#        print(f"{lx}, {ly}")
        if arr[ly][lx] == 1:
            arr[ly][lx] = 0
            Mix_PlayChannel(-1, mySounds["chomp"], 0)
            CurrentScore += 10
        elif arr[ly][lx] == 2:
            arr[ly][lx] = 0
            Mix_PlayChannel(-1, mySounds["chomp"], 0)
            CurrentScore += 50
            for k in myGhosts:
                myGhosts[k].Frighten()

        for k in myGhosts:
            gX = myGhosts[k].PosX
            gY = myGhosts[k].PosY

            if self.PosX + 16 > gX and self.PosX < gX + 16 and self.PosY + 16 > gY and self.PosY < gY + 16:
                if myGhosts[k].State == GhostState.STATE_FRIGHTENED:
                    myGhosts[k].State = GhostState.STATE_RESPAWNING
                elif myGhosts[k].State != GhostState.STATE_RESPAWNING:
                    ResetGame()

myPlayer = Player()

def PollKeyboard():
    keys = SDL_GetKeyboardState(None)
    for i in range(255):
        myFormerKeyStates[i] = myKeyStates[i]
        myKeyStates[i] = keys[i]

def IsKeyDown(which):
    return myKeyStates[which]

def IsKeyTap(which):
    return (myKeyStates[which] == True and myFormerKeyStates[which] == False)

bPreviewShown = False
def DrawEditPreview():
    r = SDL_Rect(0,0,128,128)
    c = SDL_Rect(0,0,256,256)
#    SDL_RenderCopy(myRenderer, tilesTex, c, r)


EditCursorX = 0
EditCursorY = 0
def CheckInputs():
    global myGameState, EditCursorX, EditCursorY, chomp

    iMouseX = ctypes.c_int()
    iMouseY = ctypes.c_int()
    SDL_GetMouseState(ctypes.byref(iMouseX), ctypes.byref(iMouseY))
    EditCursorX = round(iMouseX.value / 8)
#    print(f"POS- {EditCursorX}, {EditCursorY}")
    EditCursorY = round((iMouseY.value) / 8)
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

        if IsKeyTap(SDL_SCANCODE_T):
            myMaze[EditCursorY][EditCursorX] = 48

        if IsKeyTap(SDL_SCANCODE_Y):
            myMaze[EditCursorY][EditCursorX] = -1

        if IsKeyDown(SDL_SCANCODE_H):
            if myMaze[EditCursorY][EditCursorX] == -1:
                arr[EditCursorY][EditCursorX] = 1
                print(f"as- {EditCursorX}, {EditCursorY}")

        if IsKeyDown(SDL_SCANCODE_J):
            arr[EditCursorY][EditCursorX] = 0

    if IsKeyTap(SDL_SCANCODE_3):
        if myGameState != GameState.STATE_EDIT:
            myGameState = GameState.STATE_EDIT
            SDL_ShowCursor(0)
        else:
            myGameState = GameState.STATE_GAME
            SDL_ShowCursor(1)



def LoadMaze():
    global myMaze
    global arr
    with open("maze", "r") as f:
        myMaze = json.load(f)

    with open("food", "r") as f:
        arr = json.load(f)

    print("loaded")

def SaveMaze():
    global myMaze
    with open("maze", "w") as f:
        json.dump(myMaze, f)

    with open("food", "w") as f:
        json.dump(arr, f)

    print("saved...")

if SDL_Init(SDL_INIT_VIDEO | SDL_INIT_AUDIO) != 0:
	print("failed SDL_Init")

TTF_Init()

Mix_OpenAudio(44100, AUDIO_S16SYS, 2, 512)
mySounds["chomp"] = Mix_LoadWAV(b"munch_1.wav")
mySounds["start"] = Mix_LoadMUS(b"game_start.wav")
mySounds["death1"] = Mix_LoadMUS(b"death_1.wav")

#myWindow = SDL_CreateWindow(b"HelloPy", SDL_WINDOWPOS_UNDEFINED, SDL_WINDOWPOS_UNDEFINED, 244*xScale, 288*yScale, SDL_WINDOW_SHOWN)
myWindow = SDL_CreateWindow(b"HelloPy", SDL_WINDOWPOS_UNDEFINED, SDL_WINDOWPOS_UNDEFINED, 224*xScale, (248+HUD_HEIGHT + 16)*yScale, SDL_WINDOW_SHOWN)
if myWindow == None:
	print("failed SDL_CreateWindow")

myRenderer = SDL_CreateRenderer(myWindow, -1, SDL_RENDERER_ACCELERATED)
if myRenderer == None:
	print("failed SDL_CreateRenderer")

error = SDL_GetError()
print(error)
SDL_RenderSetScale(myRenderer, xScale, yScale)

myEvent = SDL_Event()

smile = SDL_LoadBMP(b"logo.bmp")
if smile == None:
    print("couldn't load logo.bmp")
smileTex = SDL_CreateTextureFromSurface(myRenderer, smile)

tilesSurf = SDL_LoadBMP(b"tiles.bmp")
if tilesSurf == None:
	print("failed to load tiles.bmp")
	
tilesTex = SDL_CreateTextureFromSurface(myRenderer, tilesSurf)

playerSurf = SDL_LoadBMP(b"pacman.bmp")
if playerSurf == None:
    print("failed to load pacman.bmp")

myFont = TTF_OpenFont(b"PressStart2P.ttf", 8)
if myFont == None:
    print("couldn't open font")

#playerTex = SDL_CreateTextureFromSurface(myRenderer, playerSurf)
#SDL_SetTextureBlendMode(playerTex, SDL_BLENDMODE_BLEND)
playerTex = LoadTexture(b"pacman.bmp")

MazeWidth = 27
MazeHeight = 30
arr = x = [[0 for i in range(MazeWidth)] for j in range(MazeHeight)] 
myMaze = [[0 for i in range(MazeWidth)] for j in range (MazeHeight)]
CurrentScore = 0

def DrawString(str, x, y, r = 255, g = 255, b = 255):
    color = SDL_Color(255,255,255)
    color.r = r
    color.g = g
    color.b = b
    color.a = 255
    surf = TTF_RenderText_Solid(myFont, str, color)
    texture = SDL_CreateTextureFromSurface(myRenderer, surf)

    Width = ctypes.c_int32()
    Height = ctypes.c_int32()
    SDL_QueryTexture(texture, None, None, ctypes.byref(Width), ctypes.byref(Height))

    r = SDL_Rect(x, y, Width, Height)
    SDL_RenderCopy(myRenderer, texture, None, r)
    
    SDL_DestroyTexture(texture)
    SDL_FreeSurface(surf)

def DrawHud():
    DrawString(b"1UP", 16, 0)
    DrawString(b"HIGH SCORE", 74, 0)
    score = f"{CurrentScore}"
    DrawString(bytes(score, "utf-8"), 122, 10)
    DrawString(b"2UP", 176, 0)

    for i in range(4):
        r = SDL_Rect((i * 16) + 16, 272, 16, 16)
        c = SDL_Rect(16,Direction.LEFT * 16,16,16)
        SDL_RenderCopy(myRenderer, playerTex, c, r)


def DrawMaze():
    global myGameState
    for x in range(28):
        for y in range(31):
            
            tileID = myMaze[y][x]
            posX = x * 8
            posY = y * 8

            if tileID != -1:
                cropX = math.floor((tileID) % 8) * 8
                cropY = math.floor((tileID) / 8) * 8

                crop = SDL_Rect(int(cropX),int(cropY),8,8)
                rect = SDL_Rect(posX, posY, 8, 8)
                rect.y += HUD_HEIGHT
                SDL_RenderCopy(myRenderer, tilesTex, crop, rect)

                SDL_SetRenderDrawColor(myRenderer, 0, 0, 255, 255)
    #            SDL_RenderDrawRect(myRenderer, rect)

    if myGameState == GameState.STATE_EDIT:
        posX = EditCursorX * 8
        posY = EditCursorY * 8
        r = SDL_Rect(posX, posY + HUD_HEIGHT, 8, 8)

        SDL_SetRenderDrawColor(myRenderer, 0, 0, 255, 255)
        SDL_RenderDrawRect(myRenderer, r)
        DrawEditPreview()


LoadMaze()
done = False

GhostProgessionTimer = SDL_GetTicks()
while done == False:
    while SDL_PollEvent(myEvent):
        if myEvent.type == SDL_QUIT:
            done = True

    SDL_SetRenderDrawColor(myRenderer, 0, 0, 0, 0)
    SDL_RenderClear(myRenderer)

    PollKeyboard()
    CheckInputs()

    if myKeyStates[SDL_SCANCODE_ESCAPE] == True:
        done = True

    if IsKeyTap(SDL_SCANCODE_SPACE):
        myGameState = GameState.STATE_STARTING
        Mix_PlayMusic(mySounds["start"], 0)

    if myGameState == GameState.STATE_STARTING and Mix_PlayingMusic() == False:
        myGameState = GameState.STATE_GAME

    DrawMaze()
    for x in range(28):
        for y in range(31):
            id = arr[y][x]
            posX = x * 8
            posY = y * 8
            if id == 1:
                SDL_SetRenderDrawColor(myRenderer,255, 255, 255, 255)
                SDL_RenderDrawPoint(myRenderer, posX + 3, posY + 3 + HUD_HEIGHT)
            elif id == 2:
                r = SDL_Rect(posX + 2, posY + 2 + HUD_HEIGHT, 4, 4)
                SDL_SetRenderDrawColor(myRenderer,255, 255, 255, 255)
                SDL_RenderDrawRect(myRenderer, r)
    
    myPlayer.Update()
    myPlayer.Draw()

    for k in myGhosts:
            myGhosts[k].Draw()
            myGhosts[k].Update()

    DrawHud()

    if myGameState == GameState.STATE_STARTING:
        DrawString(b"PLAYER ONE", 73, 112, 19, 249, 248)
        DrawString(b"READY!", 90, 160, 250, 250, 23)

    SDL_SetRenderDrawColor(myRenderer, 255, 0, 0, 255)
    SDL_RenderDrawLine(myRenderer, 90, 105 + HUD_HEIGHT, 135, 105 + HUD_HEIGHT)

    SDL_RenderPresent(myRenderer)
    

SDL_DestroyWindow(myWindow)
SDL_Quit()

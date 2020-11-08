# Pac-man - Nicole Durrant 2020
# Graphics - https://www.spriters-resource.com/arcade/pacman/ - Thank you, Superjustinbros
# Sounds - https://www.classicgaming.cc/classics/pac-man/sounds

from sdl2 import *
from sdl2.sdlmixer import *
from input import *
import math
import random
from enum import IntEnum
import json
import ctypes


class Direction(IntEnum):
    UP = 0
    DOWN = 1
    LEFT = 2
    RIGHT = 3

def LoadTexture(filename):
    surf = SDL_LoadBMP(filename)
    if surf == None:
        print(f"couldn't load {filename}")
    tex = SDL_CreateTextureFromSurface(myRenderer, surf)
    SDL_FreeSurface(surf)
    return tex

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


# The game should be split into 3 states
# TITLE is just the title screen
# GAME is when the game is live and running
# EDIT is for editing the maze and pellets etc
class GameState(IntEnum):
        STATE_TITLE = 0
        STATE_GAME = 1
        STATE_EDIT = 2

myGameState = GameState.STATE_TITLE
mySounds = { "chomp": None }
myKeyStates = [False] * 255
myFormerKeyStates = [False] * 255

class Ghost:
    def __init__(self):
        self.PosX = 0
        self.PosY = 0
        self.Name = "Spook"
        self.Texture = None
        self.Target = [ 5, 5 ]
        self.NextTile = [ 1, 0 ]
        self.CurrentDir = Direction.RIGHT
        self.LastDir = Direction.RIGHT
        self.UpdateTimer = SDL_GetTicks()
        self.DbgMode = True
        self.MoveDelta = 40


    def Update(self):

        px = self.PosX + 12
        py = self.PosY + 12
        if IsKeyTap(SDL_SCANCODE_SPACE):
            done = False
            while done == False:
                self.Target = [random.randint(0, MazeWidth-1), random.randint(0, MazeHeight-1)]
                x = self.Target[0]
                y = self.Target[1]
                if myMaze[y][x] == -1:
                    done = True

        if SDL_GetTicks() - self.UpdateTimer < 20:
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
            self.MoveDelta = 8
            aboveDist = CalcLinearDist(px, py-1, self.Target[1], self.Target[0])
            belowDist = CalcLinearDist(px, py+1, self.Target[1], self.Target[0])
            leftDist = CalcLinearDist(px-1, py-1, self.Target[1], self.Target[0])
            rightDist = CalcLinearDist(px+1, py-1, self.Target[1], self.Target[0])
#
#            print(aboveDist)
#            print(belowDist)
            print(leftDist)
            print(rightDist)
            print("truasssse")
            print("\n")

            if leftDist < rightDist:
                print("c")
                self.CurrentDir = Direction.LEFT
            elif rightDist < leftDist:
                print("d")
                self.CurrentDir = Direction.RIGHT

            

        
    def Draw(self):
        if self.Texture == None:
            self.Texture = LoadTexture(b"spook.bmp")

        cropMap = { None: 0, Direction.UP: 0, Direction.DOWN: 16, Direction.LEFT: 32, Direction.RIGHT: 48 }
        c = SDL_Rect(0,cropMap[self.CurrentDir],16,16)
        r = SDL_Rect(self.PosX + 4, self.PosY + 4, 16,16)
        SDL_RenderCopy(myRenderer, self.Texture, c, r)


        if self.DbgMode == True:
            SDL_SetRenderDrawColor(myRenderer, 0, 255, 0, 255)
            SDL_RenderDrawPoint(myRenderer, (self.Target[0] * 8) + 4, (self.Target[1] * 8) + 4)

class Player:
    def __init__(self):
        self.PosX = 0
        self.PosY = 0
        self.CurrentDir = None
        self.UpdateTimer = SDL_GetTicks()
        self.AnimTimer = SDL_GetTicks()
        self.CurrentFrame = 0
        self.bMoving = False

    def Draw(self):
        r = SDL_Rect(self.PosX + 4, self.PosY + 4, 16, 16)
        crop = SDL_Rect(0,0,16,16)
        cropMap = { None: 0, Direction.UP: 0, Direction.DOWN: 16, Direction.LEFT: 32, Direction.RIGHT: 48 }
        crop.x = self.CurrentFrame * 16
        crop.y = cropMap[self.CurrentDir]
        SDL_RenderCopy(myRenderer, playerTex, crop, r)

        if SDL_GetTicks() - self.AnimTimer < 100:
            return

        self.AnimTimer = SDL_GetTicks()
        if self.CurrentFrame == 2:
            self.CurrentFrame = 0
        else:
            self.CurrentFrame += 1

    def Update(self):
        # center positions for array indexing
        py = self.PosY + 12
        px = self.PosX + 12

        roundedX = (self.PosX == (round(self.PosX / 8) * 8))
        roundedY = (self.PosY == (round(self.PosY / 8) * 8))

    	# Update every frame here ...
        if IsKeyDown(SDL_SCANCODE_LEFT) and roundedY == True and myMaze[int((py) / 8)][int((px-5) / 8)] == -1:
            self.CurrentDir = Direction.LEFT
        elif IsKeyDown(SDL_SCANCODE_RIGHT)  and roundedY == True and myMaze[int((py) / 8)][int((px+4) / 8)] == -1:
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
        if self.CurrentDir == Direction.RIGHT and myMaze[int((py) / 8)][int((px+4) / 8)] == -1:
            self.PosX += 1
        elif self.CurrentDir == Direction.LEFT and myMaze[int((py) / 8)][int((px-5) / 8)] == -1:
            self.PosX -= 1

        elif self.CurrentDir == Direction.UP and myMaze[int((py-5) / 8)][int((px) / 8)] == -1:
            self.PosY -= 1
        elif self.CurrentDir == Direction.DOWN and myMaze[int((py+4) / 8)][int((px) / 8)] == -1:
            self.PosY += 1
        else:
            self.bMoving = False

        global arr
        lx = round((self.PosX + 8) / 8)
        ly = round((self.PosY + 8) / 8)
#        print(f"{lx}, {ly}")
        if arr[ly][lx] != 0:
            arr[ly][lx] = 0
            Mix_PlayChannel(-1, mySounds["chomp"], 0)

myPlayer = Player()
Spook = Ghost()

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
    EditCursorY = round(iMouseY.value / 8)
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

Mix_OpenAudio(44100, AUDIO_S16SYS, 2, 512)
mySounds["chomp"] = Mix_LoadWAV(b"munch_1.wav")

myWindow = SDL_CreateWindow(b"HelloPy", SDL_WINDOWPOS_UNDEFINED, SDL_WINDOWPOS_UNDEFINED, 224*1, 248*1, SDL_WINDOW_SHOWN)
if myWindow == None:
	print("failed SDL_CreateWindow")

myRenderer = SDL_CreateRenderer(myWindow, -1, SDL_RENDERER_ACCELERATED)
if myRenderer == None:
	print("failed SDL_CreateRenderer")

error = SDL_GetError()
print(error)
SDL_RenderSetScale(myRenderer, 1, 1)

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

#playerTex = SDL_CreateTextureFromSurface(myRenderer, playerSurf)
#SDL_SetTextureBlendMode(playerTex, SDL_BLENDMODE_BLEND)
playerTex = LoadTexture(b"pacman.bmp")

MazeWidth = 28
MazeHeight = 31
arr = x = [[0 for i in range(MazeWidth)] for j in range(MazeHeight)] 
myMaze = [[0 for i in range(MazeWidth)] for j in range (MazeHeight)]

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
                SDL_RenderCopy(myRenderer, tilesTex, crop, rect)

                SDL_SetRenderDrawColor(myRenderer, 0, 0, 255, 255)
    #            SDL_RenderDrawRect(myRenderer, rect)

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

    SDL_SetRenderDrawColor(myRenderer, 0, 0, 0, 0)
    SDL_RenderClear(myRenderer)

    PollKeyboard()
    CheckInputs()

    if myKeyStates[SDL_SCANCODE_ESCAPE] == True:
        done = True

    DrawMaze()
    for x in range(28):
        for y in range(31):
            id = arr[y][x]
            if id == 1:
                
                posX = x * 8
                posY = y * 8
                SDL_SetRenderDrawColor(myRenderer,255, 255, 255, 255)
                SDL_RenderDrawPoint(myRenderer, posX + 3, posY + 3)
    
    myPlayer.Update()
    myPlayer.Draw()

    # TODO: move these
    Spook.Draw()
    Spook.Update()

    SDL_RenderPresent(myRenderer)
    

SDL_DestroyWindow(myWindow)
SDL_Quit()

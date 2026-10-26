from psychopy import core, visual, event
import csv
import random
import time # TODO: or use monitor frames?


"""
Design of In-Matrix Grid:


Target: I like dogs
Result: I lik_

 [TOP] | A | B | C | D | E
  P1   | F | G | H | I | J
  P2   | K | L | M | N | O
  P3   | P | Q | R | S | T
         | U | V | W | X | Y
         | Z |SPC|DELC|DELW|END
"""

# -- CONFIG
# experiment vars
TARGET = ""
REPETITON_COUNT = 10 # Max flashes per row/col
FLASH_MS = 100 # Flash duration
ISI_MS = 75 # Stimulus onset asynchrony (SOA) of 175
CUE_MS = 1000 # How long instruction should be displayed, to focus on certain char
FEEDBACK_MS = 1000
CONFIDENCE_THRESHOLD = 0.95 # to display TOP word prediction cell

# display 
FULLSCREEN = False
DEFAULT_COLOUR = (-0.3, -0.3, -0.3) # RGB, dim-grey
FLASH_COLOUR = (1, 1, 1) # pure white, constrast to evoke P300
CUE_COLOUR = "lime" # instruction colour

# dimensions
# TODO: Decide dimensions/offset upon testing
DX, DY = 0.20, 0.15 # spacing of cells
CHAR_HEIGHT = 0.045 # height of chars
GRID_Y = -0.05 # offset of matrix from target/result


# 6x6 matrix
# TODO: Decide how to space word predictions from char inputs
GRID = [ 
    ["TOP", "A", "B", "C", "D", "E"],
    ["P1", "F", "G", "H", "I", "J"],
    ["P2", "K", "L", "M", "N", "O"],
    ["P3", "P", "Q", "R", "S", "T"],
    ["", "U", "V", "W", "X", "Y"],
    ["", "Z", "SPC", "DELC", "DELW", "END"]
]

PREDICTION_CELLS = ["TOP", "P1", "P2", "P3"]
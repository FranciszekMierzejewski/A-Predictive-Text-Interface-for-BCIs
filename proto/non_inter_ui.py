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


# -- LAYOUT
def populate_cells(window):
    """
    Mapping of name to TextSim per every non-empty cell, 
    """
    n_rows, n_cols = len(GRID), len(GRID[0])
    cells = {}

    for row_index, row in enumerate(GRID):
        for col_index, char_name in enumerate(row):
            if not char_name: # skip if empty
                continue

            # centre grid horizontally/vertically
            x = (col_index - (n_cols - 1) / 2) * DX
            y = GRID_Y - (row_index - (n_rows - 1) / 2) * DY

            # word predictions TOP/P1..P3 are placeholders, need to be empty
            cell_text = "" if char_name in PREDICTION_CELLS else char_name
            cells[char_name] = visual.TextStim(window, text=cell_text, pos=(x,y), height = CHAR_HEIGHT, color = DEFAULT_COLOUR)

    return cells 


def create_lines(matrix):   
    """
    Every row/col has a line that intensifies relevant cells

        - trigger_code: EEG trigger code to flash
        - label: readable version of code
        - names: non-empty cell name on line
    """
    lines = []

    for r_index, row in enumerate(matrix):
        names = []

        for name in row:
            if name:
                names.append(name)

        lines.append({
            "trigger_code" : r_index,
            "label" : f"R{r_index + 1}",
            "names" : [name for name in row if name]
        })

    for c_index in range(len(matrix[0])):
        names = []

        for row in matrix:
            name = row[c_index]

            if name:
                names.append(name)
            
        lines.append({
            "trigger_code" : 10 + c_index,
            "label" : f"C{c_index + 1}",
            "names" : names
        })

    return lines

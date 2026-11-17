# Constants Shared 


# -- Stimulus Timing (in milliseconds)
FLASH_MS = 100 # Flash duration
ISI_MS = 75 # Stimulus onset asynchrony (SOA) of 175
CUE_MS = 1000 # How long instruction should be displayed, to focus on certain char
FEEDBACK_MS = 1000 # Pause after selection so prediction can be read
REPETITION_COUNT = 10 # Max flashes per row/col per selection


# -- Prediction Display
CONFIDENCE_THRESHOLD = 0.95 # to display TOP word prediction cell
 

# -- Display
DEFAULT_COLOUR = (-0.3, -0.3, -0.3) # RGB, dim-grey
FLASH_COLOUR = (1, 1, 1) # pure white, constrast to evoke P300
CUE_COLOUR = "lime" # instruction colour
DX, DY = 0.20, 0.15 # cell spacing
CHAR_HEIGHT = 0.045 # height of chars
WORD_HEIGHT = 0.032 # height of word predictions
GRID_Y = -0.05 # offset of matrix from target/result
TARGET_Y = 0.46
TYPED_Y = 0.40
FULLSCREEN = False


# -- EEG
EPOCH_TMIN = 0.0 
EPOCH_TMAX = 0.8 # seconds after flash onset
EPOCH_FS = 64
BAND_HZ = (0.5, 20.0)


# -- Marker Codes
ROW_CODE_START = 1 # 1..6
COL_CODE_START = 11 # 11..16
EVENT_CUE = 101
EVENT_FEEDBACK = 102


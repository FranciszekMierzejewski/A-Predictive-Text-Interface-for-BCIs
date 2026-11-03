import csv
import random
import time
from functools import partial
 
from psychopy import core, event, visual
 
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
 
STAGE 1: non-interactive, uniform (fixed repetitions), copy-spelling, no EEG.
Run from the Coder window. ESC aborts; the log is still saved.
"""
 
# -- CONFIG
# experiment vars
TARGET = "I like dogs"
REPETITION_COUNT = 10       # blocks per character; each block flashes every row/col once
FLASH_MS = 100              # flash duration
ISI_MS = 75                 # gap between flashes -> SOA of 175
CUE_MS = 1000               # target cue shown before flashing
PAUSE_MS = 1000             # blank pause before/after flashing
FEEDBACK_MS = 1000
CONFIDENCE_THRESHOLD = 0.95  # to display TOP word prediction cell
 
# display
FULLSCREEN = False
DEFAULT_COLOUR = (-0.3, -0.3, -0.3)  # dim grey
FLASH_COLOUR = (1, 1, 1)
CUE_COLOUR = "lime"
 
# dimensions (height units)
DX, DY = 0.20, 0.15
CHAR_HEIGHT = 0.045
GRID_Y = -0.05
 
# trigger codes (never 0: 0 is the idle level on a parallel port)
ROW_CODE_BASE = 11          # rows 11-16
COL_CODE_BASE = 21          # cols 21-26
CUE_CODE = 90
 
GRID = [
    ["TOP", "A", "B", "C", "D", "E"],
    ["P1", "F", "G", "H", "I", "J"],
    ["P2", "K", "L", "M", "N", "O"],
    ["P3", "P", "Q", "R", "S", "T"],
    ["", "U", "V", "W", "X", "Y"],
    ["", "Z", "SPC", "DELC", "DELW", "END"],
]
 
PREDICTION_CELLS = ["TOP", "P1", "P2", "P3"]
 
 
# -- LAYOUT
def populate_cells(window):
    """Mapping of name to TextStim per every non-empty cell."""
    n_rows, n_cols = len(GRID), len(GRID[0])
    cells = {}
 
    for row_index, row in enumerate(GRID):
        for col_index, char_name in enumerate(row):
            if not char_name:
                continue
 
            x = (col_index - (n_cols - 1) / 2) * DX
            y = GRID_Y - (row_index - (n_rows - 1) / 2) * DY
 
            # word predictions TOP/P1..P3 start empty
            cell_text = "" if char_name in PREDICTION_CELLS else char_name
            cells[char_name] = visual.TextStim(
                window, text=cell_text, pos=(x, y),
                height=CHAR_HEIGHT, color=DEFAULT_COLOUR)
 
    return cells
 
 
def create_lines(matrix):
    """
    Every row/col is a flashable line.
        - trigger_code: EEG trigger code sent at flash onset
        - label: readable version of code
        - names: non-empty cell names on the line
    """
    lines = []
 
    for r_index, row in enumerate(matrix):
        lines.append({
            "trigger_code": ROW_CODE_BASE + r_index,
            "label": f"R{r_index + 1}",
            "names": [name for name in row if name],
        })
 
    for c_index in range(len(matrix[0])):
        lines.append({
            "trigger_code": COL_CODE_BASE + c_index,
            "label": f"C{c_index + 1}",
            "names": [row[c_index] for row in matrix if row[c_index]],
        })
 
    return lines
 
 
def permutation(flashing_lines, repetition_count: int = REPETITION_COUNT):
    """
    repetition_count blocks, each a random permutation of every line.
    The same line never flashes twice in a row across block borders.
    """
    flash_order = []
 
    for _ in range(repetition_count):
        block = flashing_lines[:]
        while True:
            random.shuffle(block)
            if not flash_order or block[0] is not flash_order[-1]:
                break
        flash_order.extend(block)
 
    return flash_order
 
 
# -- Speller Logic
def char_to_cell(char):
    char = char.upper()
    return "SPC" if char == " " else char
 
 
def apply_cell(result, cell):
    """Apply cell choice to result."""
    if cell == "SPC":
        return result + " "
    elif cell == "DELC":
        return result[:-1]
    elif cell == "DELW":
        # delete last word AND any trailing spaces, keep the space before it
        words = result.rstrip().split(" ")
        return " ".join(words[:-1]) + (" " if len(words) > 1 else "")
    elif len(cell) == 1:
        return result + cell
    return result  # TODO: END / prediction cells
 
 
def make_predictions(result):
    """
    Cost-minimisation / language model goes here.
    Return [(word, probability), ...] in descending order.
    """
    return []
 
 
def show_predictions(cells, predictions: list[tuple[str, float]]):
    """
    If the best prediction clears CONFIDENCE_THRESHOLD it fills TOP and
    P1-3 take predictions 2-4; otherwise TOP is empty and P1-3 take 1-3.
    Call only BETWEEN flash sequences, never during one.
    """
    if predictions and predictions[0][1] >= CONFIDENCE_THRESHOLD:
        top = predictions[0][0]
        candidates = [word for word, _ in predictions[1:4]]
    else:
        top = ""
        candidates = [word for word, _ in predictions[:3]]
 
    candidates += [""] * (3 - len(candidates))
 
    for name, word in zip(PREDICTION_CELLS, [top] + candidates):
        cells[name].text = word
 
 
def decode_cell(target):
    """
    STAGE 1: returns the target, so the Result line is fake feedback.
    LATER: replace with posterior argmax from simulated/real EEG evidence.
    """
    return target
 
 
# -- TIMING / LOGGING
def send_trigger(code):
    """STUB: parallel port / serial / LSL marker goes here."""
    pass
 
 
def mark(log, clock, code, **info):
    send_trigger(code)
    log.append(dict(t=clock.getTime(), code=code, **info))
 
 
def save_log(log, path):
    if not log:
        return
    fields = ["t", "code", "char_idx", "target", "line", "is_target"]
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, restval="")
        writer.writeheader()
        writer.writerows(log)
 
 
def audit_timing(log, soa_ms):
    """Inter-flash intervals (flip-locked) vs the intended SOA, within a character."""
    flashes = [e for e in log if ROW_CODE_BASE <= e["code"] < COL_CODE_BASE + 6]
    gaps = [(b["t"] - a["t"]) * 1000
            for a, b in zip(flashes, flashes[1:])
            if a["char_idx"] == b["char_idx"]]
    if not gaps:
        return
    mean = sum(gaps) / len(gaps)
    sd = (sum((g - mean) ** 2 for g in gaps) / len(gaps)) ** 0.5
    print(f"SOA intended {soa_ms:.1f} ms | measured mean {mean:.1f}, SD {sd:.2f}, "
          f"min {min(gaps):.1f}, max {max(gaps):.1f}")
 
 
# -- PRESENTATION
def show_frames(window, scene, n_frames, on_first_flip=None):
    """Draw scene for exactly n_frames. Timing is counted in frames, not seconds."""
    for frame in range(n_frames):
        for stim in scene:
            stim.draw()
        if frame == 0 and on_first_flip is not None:
            window.callOnFlip(on_first_flip)
        window.flip()
        if "escape" in event.getKeys(["escape"]):
            raise KeyboardInterrupt
 
 
def run_flashes(window, scene, cells, lines, target, char_index, log, clock,
                flash_frames, isi_frames):
    for line in permutation(lines):
        stims = [cells[name] for name in line["names"]]
        for stim in stims:
            stim.color = FLASH_COLOUR
 
        onset = partial(mark, log, clock, line["trigger_code"],
                        char_idx=char_index, target=target, line=line["label"],
                        is_target=int(target in line["names"]))
        show_frames(window, scene, flash_frames, on_first_flip=onset)
 
        for stim in stims:
            stim.color = DEFAULT_COLOUR
        show_frames(window, scene, isi_frames)
 
 
def main():
    valid = {name for row in GRID for name in row if name}
    targets = [char_to_cell(ch) for ch in TARGET]
    missing = [t for t in targets if t not in valid]
    if missing:
        raise ValueError(f"Not in matrix: {missing}")
 
    window = visual.Window(size=(1000, 700), color="black", units="height",
                           fullscr=FULLSCREEN, allowGUI=False)
    window.recordFrameIntervals = True
    cells = populate_cells(window)
    lines = create_lines(GRID)
 
    rate = window.getActualFrameRate() or 60.0
    frames = lambda ms: max(1, round(ms * rate / 1000))
    flash_frames, isi_frames = frames(FLASH_MS), frames(ISI_MS)
    soa_ms = (flash_frames + isi_frames) * 1000 / rate
    print(f"{rate:.1f} Hz | flash {flash_frames} f, ISI {isi_frames} f | SOA {soa_ms:.1f} ms")
 
    target_stim = visual.TextStim(window, text=f"Target: {TARGET}", pos=(-0.6, 0.46),
                                  height=0.045, anchorHoriz="left", color="white")
    result_stim = visual.TextStim(window, text="Result: _", pos=(-0.6, 0.41),
                                  height=0.045, anchorHoriz="left", color="white")
    scene = [target_stim, result_stim] + list(cells.values())
 
    log, clock, result = [], core.Clock(), ""
    log_path = time.strftime("p300_log_%Y%m%d_%H%M%S.csv")
 
    try:
        show_frames(window, scene, frames(PAUSE_MS))
        for char_index, target in enumerate(targets):
            show_predictions(cells, make_predictions(result))
 
            # cue
            cells[target].color = CUE_COLOUR
            cue_mark = partial(mark, log, clock, CUE_CODE, char_idx=char_index, target=target)
            show_frames(window, scene, frames(CUE_MS), on_first_flip=cue_mark)
            cells[target].color = DEFAULT_COLOUR
            show_frames(window, scene, frames(PAUSE_MS))
 
            # flashing
            run_flashes(window, scene, cells, lines, target, char_index, log, clock,
                        flash_frames, isi_frames)
 
            # feedback
            show_frames(window, scene, frames(PAUSE_MS))
            result = apply_cell(result, decode_cell(target))
            result_stim.text = f"Result: {result}_"
            show_frames(window, scene, frames(FEEDBACK_MS))
    except KeyboardInterrupt:
        print("Aborted by user.")
    finally:
        print(f"Dropped frames: {window.nDroppedFrames}")
        audit_timing(log, soa_ms)
        save_log(log, log_path)
        window.close()
        core.quit()
 
 
if __name__ == "__main__":
    main()
    
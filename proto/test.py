"""
P300 row/column speller - copy-spelling (calibration) mode.


Run from the PsychoPy Coder window (green "Run" button) or: python p300_speller.py
Press ESC at any time to abort; the event log is still saved.


This script ONLY presents stimuli and logs flip-locked event markers.
There is no EEG acquisition and no classifier here (see decode_selection).
"""
import csv
import random
import time
from functools import partial


from psychopy import core, event, visual


# ----------------------------- CONFIG ---------------------------------------
TARGET_TEXT = "I like dogs"
N_REPS = 10             # blocks per character; each block = every row+col once
FLASH_MS = 100          # stimulus on-time
ISI_MS = 75             # gap between flashes  -> SOA = 175 ms
CUE_S = 2.0             # target cue shown in green
PAUSE_S = 1.0           # blank pause before/after flashing
FEEDBACK_S = 1.0
FULLSCREEN = False
CONF_THRESHOLD = 0.90   # [TOP] only appears at/above this model confidence


DIM_COLOR = (-0.3, -0.3, -0.3)
FLASH_COLOR = (1, 1, 1)
CUE_COLOR = 'lime'


DX, DY = 0.16, 0.11     # cell spacing (height units)
LETTER_H = 0.045
GRID_Y = -0.04          # vertical offset of the matrix


# 6x6 matrix: column 0 holds word predictions, columns 1-5 the speller proper.
GRID = [
    ['[TOP]', 'A', 'B', 'C', 'D', 'E'],
    ['P1',    'F', 'G', 'H', 'I', 'J'],
    ['P2',    'K', 'L', 'M', 'N', 'O'],
    ['P3',    'P', 'Q', 'R', 'S', 'T'],
    ['',      'U', 'V', 'W', 'X', 'Y'],
    ['',      'Z', 'SPC', 'DELC', 'DELW', 'END'],
]
PRED_CELLS = ['[TOP]', 'P1', 'P2', 'P3']



# ----------------------------- LAYOUT ---------------------------------------
def build_cells(win):
    """One TextStim per non-empty cell, keyed by cell name."""
    n_rows, n_cols = len(GRID), len(GRID[0])
    cells = {}
    for r, row in enumerate(GRID):
        for c, name in enumerate(row):
            if not name:
                continue
            x = (c - (n_cols - 1) / 2) * DX
            y = GRID_Y - (r - (n_rows - 1) / 2) * DY
            text = '' if name in PRED_CELLS else name   # predictions start empty
            cells[name] = visual.TextStim(win, text=text, pos=(x, y),
                                          height=LETTER_H, color=DIM_COLOR)
    return cells



def build_lines(grid):
    """Every row and column as a flashable 'line' with its own trigger code."""
    lines = [dict(code=11 + r, label=f'R{r + 1}', names=[n for n in row if n])
             for r, row in enumerate(grid)]
    for c in range(len(grid[0])):
        lines.append(dict(code=21 + c, label=f'C{c + 1}',
                          names=[row[c] for row in grid if row[c]]))
    return lines



def make_sequence(lines, n_reps):
    """n_reps blocks, each a random permutation of all lines.
    Prevents the same line flashing twice in a row across block borders."""
    order = []
    for _ in range(n_reps):
        block = lines[:]
        while True:
            random.shuffle(block)
            if not order or block[0] is not order[-1]:
                break
        order.extend(block)
    return order



# ----------------------------- SPELLER LOGIC --------------------------------
def char_to_cell(ch):
    ch = ch.upper()
    return 'SPC' if ch == ' ' else ch



def apply_selection(text, name):
    if name == 'SPC':
        return text + ' '
    if name == 'DELC':
        return text[:-1]
    if name == 'DELW':
        words = text.rstrip().split(' ')
        return ' '.join(words[:-1]) + (' ' if len(words) > 1 else '')
    if len(name) == 1:
        return text + name
    return text    # END, and prediction cells (not implemented)



def get_predictions(text):
    """STUB. Return [(word, probability), ...], best first."""
    return []



def update_predictions(cells, preds):
    """P1-P3 show the top 3 candidates; [TOP] only if the best one clears
    CONF_THRESHOLD."""
    words = [w for w, _ in preds[:3]] + [''] * 3
    top = preds[0][0] if preds and preds[0][1] >= CONF_THRESHOLD else ''
    for name, word in zip(PRED_CELLS, [top] + words[:3]):
        cells[name].text = word



def decode_selection(target_name):
    """CALIBRATION MODE: returns the target (feedback is therefore fake).
    ONLINE MODE: epoch the EEG after each flash, score each row/column with
    your classifier, take argmax row + argmax column -> cell at the
    intersection, and return that name instead."""
    return target_name



# ----------------------------- TIMING / LOGGING -----------------------------
def send_trigger(code):
    """STUB: parallel port / serial / LSL marker goes here."""
    pass



def mark(log, clock, code, **info):
    send_trigger(code)
    log.append(dict(t=clock.getTime(), code=code, **info))



def save_log(log, path):
    if not log:
        return
    fields = ['t', 'code', 'char_idx', 'target', 'line', 'is_target']
    with open(path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields, restval='')
        w.writeheader()
        w.writerows(log)



def check_quit():
    if 'escape' in event.getKeys(['escape']):
        raise KeyboardInterrupt



def show_frames(win, scene, n_frames, on_first_flip=None):
    """Draw the scene for exactly n_frames. Timing is counted in frames,
    never with core.wait()."""
    for f in range(n_frames):
        for stim in scene:
            stim.draw()
        if f == 0 and on_first_flip is not None:
            win.callOnFlip(on_first_flip)
        win.flip()
        check_quit()



def run_flashes(win, scene, cells, lines, target, char_idx, log, clock,
                flash_f, isi_f):
    for line in make_sequence(lines, N_REPS):
        stims = [cells[n] for n in line['names']]
        for s in stims:
            s.color = FLASH_COLOR
        cb = partial(mark, log, clock, line['code'], char_idx=char_idx,
                     target=target, line=line['label'],
                     is_target=int(target in line['names']))
        show_frames(win, scene, flash_f, on_first_flip=cb)
        for s in stims:
            s.color = DIM_COLOR
        show_frames(win, scene, isi_f)



# ----------------------------- MAIN -----------------------------------------
def main():
    targets = [char_to_cell(ch) for ch in TARGET_TEXT]


    win = visual.Window(size=(1000, 700), color='black', units='height',
                        fullscr=FULLSCREEN, allowGUI=False)
    win.recordFrameIntervals = True
    cells = build_cells(win)
    lines = build_lines(GRID)
    for t in targets:
        if t not in cells:
            raise ValueError(f'"{t}" is not in the matrix')


    rate = win.getActualFrameRate() or 60.0
    frames = lambda ms: max(1, round(ms * rate / 1000))
    flash_f, isi_f = frames(FLASH_MS), frames(ISI_MS)
    print(f'{rate:.1f} Hz | flash {flash_f} f, ISI {isi_f} f | '
          f'SOA {(flash_f + isi_f) * 1000 / rate:.0f} ms')


    target_stim = visual.TextStim(win, text=f'Target: {TARGET_TEXT}',
                                  pos=(-0.6, 0.43), height=0.045,
                                  anchorHoriz='left', color='white')
    result_stim = visual.TextStim(win, text='Result: _', pos=(-0.6, 0.37),
                                  height=0.045, anchorHoriz='left',
                                  color='white')
    scene = [target_stim, result_stim] + list(cells.values())


    log, clock, result = [], core.Clock(), ''
    log_path = time.strftime('p300_log_%Y%m%d_%H%M%S.csv')


    try:
        show_frames(win, scene, frames(PAUSE_S * 1000))
        for idx, target in enumerate(targets):
            update_predictions(cells, get_predictions(result))


            cells[target].color = CUE_COLOR                  # cue
            show_frames(win, scene, frames(CUE_S * 1000))
            cells[target].color = DIM_COLOR
            show_frames(win, scene, frames(PAUSE_S * 1000))


            run_flashes(win, scene, cells, lines, target, idx, log, clock,
                        flash_f, isi_f)                      # flashing


            show_frames(win, scene, frames(PAUSE_S * 1000))
            result = apply_selection(result, decode_selection(target))
            result_stim.text = f'Result: {result}_'
            show_frames(win, scene, frames(FEEDBACK_S * 1000))
    except KeyboardInterrupt:
        print('Aborted by user.')
    finally:
        print(f'Dropped frames: {win.nDroppedFrames}')
        save_log(log, log_path)
        win.close()
        core.quit()



if __name__ == '__main__':
    main()
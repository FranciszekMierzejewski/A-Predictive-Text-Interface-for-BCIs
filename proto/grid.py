import random
from dataclasses import dataclass
import settings 

GRID = [
    ["TOP", "A", "B", "C", "D", "E"],
    ["P1", "F", "G", "H", "I", "J"],
    ["P2", "K", "L", "M", "N", "O"],
    ["P3", "P", "Q", "R", "S", "T"],
    ["", "U", "V", "W", "X", "Y"],
    ["", "Z", "SPC", "DELC", "DELW", "END"]
]

PREDICTION_CELLS = ("TOP", "P1", "P2", "P3")


@dataclass(frozen = True) # Auto generates constructor, frozen makes instances immutable
class Line:
    code: int # marker sent to EEG
    label: str # R1..6, C1..6
    names = tuple[str] # All possible cells on line


def all_cells(grid = GRID) -> list[str]: # iter over
    return [name for row in grid for name in row if name]


def visible_cells(shown = None, grid = GRID) -> list[str]:
    """
    Cells user can select, i.e. fixed with TOP..P3 predictions
    """
    shown = shown or {} 
    return [cell for cell in all_cells(grid) if cell not in PREDICTION_CELLS or shown.get(cell)]


def create_lines(grid = GRID) -> list[Line]:
    lines = [Line(settings.ROW_CODE_START + row_index, f"R{row_index + 1}", tuple(non_empty for non_empty in grid if non_empty)) for row_index, row in enumerate(grid)]

    for col in range(len(grid[0])):
        lines.append(Line(settings.COL_CODE_START + col, f"C{col + 1}", tuple(row[col] for row in grid if row[c])))

    return lines


def active_lines(lines: list[Line], shown: dict[str, str]) -> list[Line]:
    """
    For now, just an implementation against None. TODO if low probability given to cells in line, skip
    """
    visible = set(visible_cells(shown))
    active = []

    for line in lines:
        names = tuple(cell_name for cell_name in line.names if cell_name in visible) 

        if names:
            active.append(Line(line.code, line.label, names))

    return active


def repetitions(lines: list[Line], max_repetitions = settings.MAX_REPETITIONS):
    # TODO check again if previous implementation of permutation works? every row shares a cell with ever col?

    random_number_generator = random.Random()

    previous_last = None

    for _ in range(max_repetitions):
        block = list(lines)
        random_number_generator.shuffle(block) # modifies list to randomnly rearrange elements

        if previous_last is not None and len(block) > 1 and block[0].code == previous_last.code: # check if start and end is same, i.e  repeating
            j = random_number_generator.randrange(1, len(block)) # selects random integer
            block[0], block[j] = block[j], block[0]
        previous_last = block[-1]

        yield block # generate a repetition, wait until another request via next(generator)


# -- Text
def last_word(result_text: str) -> str:
    # Split currently typed text from the right, with a space seperator, splitting at most once to get latest word being typed
    return result_text.rsplit(" ", 1)[-1] # ['original words', 'currently_typed_word']


def delete_last_word(result_text: str) -> str:
    words = result_text.rstrip().split(" ") # Remove whitespace from right
    return " ".join(words[:-1]) + " " if len(words) > 1 else " " # automatically add a space after word removal to save SPC time


def apply_cell(result_text: str, cell: str, shown: dict[str, str]) -> tuple[str, bool]:
    """
    Apply cell selection to result text. Returns lowercase text result and finished state tuple
    """
    shown = shown or {}

    if cell == "SPC":
        return result_text + ' ', False
    elif cell == "DELC":
        return result_text[:-1], False
    elif cell == "DELW":
        return delete_last_word(result_text), False
    elif cell == "END":
        return result_text, True
    elif cell in PREDICTION_CELLS:
        word = shown.get(cell, "")

        if not word:
            return result_text, False

        return result_text[: len(result_text) - len(last_word(result_text))] + word + " ", False # keep everything up to currently written word, then replace with prediction
    elif len(cell) == 1: 
        return result_text + cell.lower(), False # manually entered letter
    return result_text, False # fallback, if unknown cmd ignore


def show_predictions(ranked_predictions: list[tuple[str, float]], threshold: float = settings.CONFIDENCE_THRESHOLD) -> dict[str, str]:
    shown = {cell: "" for cell in PREDICTION_CELLS}

    if not ranked_predictions:
        return shown
    elif ranked_predictions[0][1] >= threshold: # if over threshold, add TOP prediction
        shown["TOP"] = ranked_predictions[0][1]
        other_predictions = ranked_predictions[1:4]
    else:
        other_predictions = ranked_predictions[:3]

    for cell, (word, probability) in zip((PREDICTION_CELLS[1:4]), other_predictions):
        shown[cell] = word

    return shown


def best_selection(target: str, result_text: str, shown: dict[str, str], use_predictions: bool = True) -> str:
    """
    Remember trigated confidence, means using predictions may not be possible. Finds optimal selection
    """

    if result_text == target:
        return "END"
    
    if not target.startswith(result_text):
        if result_text.rstrip() == target: # in instance where user selections a prediction, we have an extra space at end, so remove
            return "END" # match

        # TODO: create a DELW optimisation algorithm.
        # e.g. when comparing target and result, if:
        #   a single character wrong at start, then saves time to use DELW than repeatedly DELC
        #   if character is wrong second-to-last, then using DELC twice may save time over using DELW once and retyping everything again.
        # need to consider multiple wrong characters, and for cases with use prediction flag on and off.

        return "DELC" 

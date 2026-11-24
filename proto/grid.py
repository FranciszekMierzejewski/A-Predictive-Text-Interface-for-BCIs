import random
import settings 

from dataclasses import dataclass
from collections import deque

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


def _optimal_deletion(target: str, result_text: str) -> tuple[int, str]:
    """
    Using BFS to find optimal deletion, assuming each deletion costs 1, retyping each character costs 1
    
    """
    best_key = (float("inf"), float("inf")) # ()
    best_action = "DELC" # default
    visited = {result_text}
    queue = deque([(result_text, 0, None)]) # (current_text after deletions, cost of deletions, first action taken)

    while queue: # explores every reachable state until empty
        current_text, cost, first_action = queue.popleft() # take oldest state from queue

        if first_action is not None and target.startswith(current_text): # check if current word is a prefix of target, and deletion performed
            key = (cost + len(target) - len(current_text), cost) # original cost + additional characters typed

            if key < best_key: # compares tuple lexicographically, prioritises least total actions, least deletions if tie
                best_key, best_action = key, first_action # we care about first action only
            continue # exploring further deletions from current state is pointless, given deletion only increases cost

        for action in ("DELC", "DELW"): # explores each deletion action from current state
            next_text, finished_state = apply_cell(current_text, action, {})

            if next_text not in visited: # explores unique states only
                visited.add(next_text) # add to visited
                queue.append((next_text, cost + 1, first_action or action)) 

    return int(best_key[0]), best_action # returns minimum total cost with best action


def _optimal_prediction(target: str, result_text: str, shown: dict[str, str]):
    """
    Cheapest valid prediction from current state.
    """
    start_index_last_word = len(result_text) - len(last_word(result_text))

    if not target.startswith(result_text[:start_index_last_word]): # if current text is not a prefix of target, prediction cannot fix it
        return None

    best_prediction = None

    for cell in PREDICTION_CELLS:
        word = shown.get(cell, "") # get prediction

        if not word:
            continue

        new_word = result_text[:start_index_last_word] + word.lower() + " " # Prediction completes word and adds space

        if target.startswith(new_word) or new_word.rstrip() == target: # verify prefix match
            total_cost = 1 + max(0, len(target) - len(new_word)) # update total cost, which includes distance away from target

            if best_prediction is None or total_cost < best_prediction[0]: # update least cost
                best_prediction = (total_cost, cell)

    return best_prediction # (total cost, cell)


def best_selection(target: str, result_text: str, shown: dict[str, str], use_predictions: bool = True) -> str:
    """
    Remember trigated confidence, means using predictions may not be possible. Finds optimal selection
    """

    target, result_text = target.lower(), result_text.lower()

    if result_text == target or result_text.rstrip() == target: # target met
        return "END"


    prediction = _optimal_prediction(target, result_text, shown or {}) if use_predictions else None # if predictions on, find optimal

    if target.startswith(result_text): # check prefix
        character_typing_cost = len(target) - len(result_text) # cost of manual typing

        if prediction and prediction[0] < character_typing_cost: # compare prediction for None edgecase to not raise TypeError when trying to access index 0, TODO decide if <=, i.e. favour predictions?
            return prediction[1]

        next_character = target[len(result_text)]
        return "SPC" if next_character == " " else next_character.upper() # return next manual char, no deleting if prior chars correct

    deletion_minimum_cost, deletion_action = _optimal_deletion(target, result_text)

    if prediction and prediction[0] <= deletion_minimum_cost(target, result_text):
        return prediction[1]

    return deletion_action

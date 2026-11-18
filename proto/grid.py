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
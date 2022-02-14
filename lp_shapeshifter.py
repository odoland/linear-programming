from pulp import *
from itertools import product


def can_place(board, piece, r, c):
    height = len(piece)
    width = len(piece[0])
    return ((r + height) <= len(board)) and ((c + width) <= len(board[0]))


def all_coordinates(board):
    yield from product(range(len(board)), range(len(board[0])))


def map_cells_to_pieces(piece_vars, board, pieces):
    """Maps each coordinate on the board with all the piece(s) that could touch it if they were placed.

    The returned touched_by is a list of decision variables that will influence a particular (r, c) on the board. 
    """

    touched_by = {(r, c): [] for r, c in all_coordinates(board)}
    for pid, piece in enumerate(pieces):
        rows, cols = len(piece), len(piece[0])
        cells = [
            (r, c) for r, c in product(range(rows), range(cols)) if piece[r][c] == 1
        ]
        placements = [
            (r, c) for r, c in all_coordinates(board) if can_place(board, piece, r, c)
        ]
        for r, c in placements:
            for dy, dx in cells:
                touched_by[(r + dy, c + dx)].append(piece_vars[pid][r][c])
    return touched_by


def each_piece_used_once(piece_vars, board, pieces):
    """Constraints for each piece being used exactly once on the board. """
    for pid, piece in enumerate(pieces):
        placeable_positions = [
            piece_vars[pid][r][c]
            for r, c in all_coordinates(board) if can_place(board, piece, r, c)
        ]
        # Since all are binary (0 or 1), the sum of all placeable positions equaling 1
        # indicates that only one position was used.
        yield lpSum(placeable_positions) == 1


def all_cells_are_zero(touched_by, board, flips, pieces):
    """Constraints for each coordinate on the board, after placing all pieces, end up as the 0 shape. """
    board_coords = list(all_coordinates(board))

    # The equation board[r][c] % flips == 0 is equivalent to
    # board[r][c] == m * flips for all values of m.
    # but we can further constraint the value of m
    kw = dict(
        lowBound=0,
        # This upperbound occurs when all pieces touch the same (r, c) spot
        upBound=(len(pieces) + 1) // flips,
        cat=LpInteger,
    )
    m = {(r, c): LpVariable(f"I{r},{c}", **kw) for r, c in board_coords}

    for r, c in board_coords:
        if touched_by[(r, c)]:
            initial_state = [board[r][c]]
            divisable_by_flips = (
                lpSum(touched_by[(r, c)] + initial_state) == m[(r, c)] * flips
            )
            yield divisable_by_flips


def apply_piece(board, piece, r, c):
    for i in range(len(piece)):
        for j in range(len(piece[i])):
            if piece[i][j] == 1:
                board[r + i][c + j] += 1


def apply_solution(board, piece_placements_var, pieces):
    for i, piece_var in enumerate(piece_placements_var):
        for r, c in all_coordinates(board):
            if piece_var[r][c].value() == 1:
                # print(f"Place piece {i} at col {c} row {r}")
                apply_piece(board, pieces[i], r, c)


def print_board(board, flips):
    for row in board:
        for cell in row:
            print(cell % flips, end="")
        print()


def parse_input(board, pieces):
    board = [[int(x) for x in row] for row in board.split(",")]
    pieces = pieces.replace("X", "1").replace(".", "0").split(" ")
    pieces = [[[int(x) for x in row] for row in piece.split(",")]
              for piece in pieces]
    return board, pieces


def solve(board, pieces, flips):
    """Solves the shapeshifter by modeling it as a linear optimization problem and prints to stdout. 

    Let m, n be the dimensions of the board, and pid be each piece.

    Decision variables:
    - piece_row_col: Each piece has m x n binary decision variable of whether that piece was placed.

      We do not need to care about the order of placing the pieces. Placement of a piece is modeled
      as addition, which is communnative.

    Constraints:
    - each_piece_used_once: Each piece can only be used once. That is, for any given pid, there can be only one pid_r_c that is == 1
    - all_cells_are_zero: For each coordinate on the board, the ending position must be the "0" shape. That is, the sum of all pieces that touched it must be evenly divisible by 5. 

    """
    prob = LpProblem("Shapeshifter", const.LpMinimize)
    # Represents a piece (pid) and all its possible placement positions for every row, column.
    piece_row_col = [
        [
            [
                LpVariable(f"P{pid}_{row}_{col}", cat=const.LpBinary)
                for col in range(len(board[0]))
            ]
            for row in range(len(board))
        ]
        for pid in range(len(pieces))
    ]
    for constraint in each_piece_used_once(piece_row_col, board, pieces):
        prob += constraint
    touched_by = map_cells_to_pieces(piece_row_col, board, pieces)
    for constraint in all_cells_are_zero(touched_by, board, flips, pieces):
        prob += constraint

    prob.solve()
    print(LpStatus[prob.status])
    apply_solution(board, piece_row_col, pieces)
    print_board(board, flips)


if __name__ == "__main__":
    import time

    start = time.time()

    board = "0040040400000,4434244404040,4433242322330,0040443314340,0000004010244,0004043442044,0003434302334,0444334004030,4403334004444,0333400404334,0040044440404,0040004444000,0434000403440,0404000444000"
    pieces = ".X.X,XX.X,.XXX,XX.. XXX ..X,XXX,X.. XXX,X..,X.. X,X,X X.X,XXX X..,XX.,.XX XX,XX XX X.X,XXX,X.X .XXX,..X.,XXX. X.X,XXX X..,XXX,..X X XX.X,X..X,XXXX,..X. XX.,.XX X.X,XXX,X.X XX.,.XX X.X,X.X,XXX XXX,X.X,XXX .X..,XX.X,.XXX ...X,X.XX,X.X.,XXX.,X.X. XXX,X.X X.X,XXX XXXX,X...,X... X..,XX.,.XX .XX.,XX..,.XXX XXX.,..XX,XXX.,.X..".replace(
        ".", "0"
    )
    flips = 5
    board, pieces = parse_input(board, pieces)

    solve(board, pieces, flips)

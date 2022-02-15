import random
from pulp import *
from itertools import product, chain
from typing import Dict, Generator, Tuple

# Represents a (row, col) coordinate on the board
Coord = Tuple[int, int]
# Solution is a mapping of coordinate to times pressed
Solution = Dict[Coord, int]
Board = list[list[int]]

# Maps coordinate to the corresponding decision variable
DecisionVars = Dict[Coord, LpVariable]

# Cross shape neighbors from hitting a light:
#  x
# xxx
#  x
neighbor_offsets: Coord = [
    (0, 0),
    (0, 1),
    (1, 0),
    (-1, 0),
    (0, -1),
]


def generate_board(m: int, n: int, moves: int) -> Board:
    """Generates a solvable lights out initial board state."""
    board = [[0 for _ in range(m)] for _ in range(n)]
    for _ in range(moves):
        row = random.randint(0, m-1)
        col = random.randint(0, n-1)
        hit_light(board, row, col)
    return board


def hit_light(board: Board, r: int, c: int, times=1):
    """Simulates a pressing a light on row c, col c on the board."""
    for dy, dx in neighbor_offsets:
        y, x = r + dy, c + dx
        if in_bounds(y, x, m, n):
            board[r + dy][c + dx] += times
            board[r + dy][c + dx] %= 2


def all_coords(m: int, n: int) -> Generator[Coord, None, None]:
    """Yields all the coordiantes of a M x N board. """
    return product(range(m), range(n))


def in_bounds(r: int, c: int, m: int, n: int) -> bool:
    """Whether a row, col is within the bounds of an M x N board."""
    return (0 <= r < m) and (0 <= c < n)


def get_all_neighbors(r: int, c: int, m: int, n: int) -> Generator[Coord, None, None]:
    """Returns the coordinates of the neighboring cells plus the current coordinate."""
    for dy, dx in neighbor_offsets:
        if in_bounds(r+dy, c+dx, m, n):
            yield (r+dy, c+dx)


def print_board(board: Board):
    for row in board:
        for col in row:
            print("■" if col else "□", end="")
        print()


def lights_out_constraints(placement_vars: Dict[Coord, LpVariable], initial_board: list[list[int]]) -> Generator[LpConstraint, None, None]:
    m, n = len(initial_board), len(initial_board[0])

    factor = {(r, c):  LpVariable(f"c{r},{c}", lowBound=0, cat=const.LpInteger)
              for r, c in all_coords(m, n)}

    for r, c in all_coords(m, n):
        initial_state = [initial_board[r][c]]
        cross_touching = [placement_vars[(y, x)]
                          for y, x in get_all_neighbors(r, c, m, n)]
        yield lpSum(initial_state + cross_touching) == 2 * factor[r, c]


def minimize_moves_objective(placement_vars):
    return lpSum(list(placement_vars.values()))


def get_solution(placement_vars) -> Solution:
    solution = {}
    for (r, c), decision_var in placement_vars.items():
        times = decision_var.value()
        if times > 0:
            solution[(r, c)] = times
    return solution


def apply_solution(board, solution: Solution) -> bool:
    for (r, c), times in solution.items():
        hit_light(board, r, c, times=times)

    return sum(chain(*board)) == 0


def solve(board: Board) -> Solution | None:
    """Models lights out game as a linear optimization problem."""
    m, n = len(board), len(board[0])
    problem = LpProblem("LightsOut", LpMinimize)

    placement_vars = {(r, c): LpVariable(f"m{r},{c}", lowBound=0, cat=const.LpInteger)
                      for r, c in all_coords(m, n)}

    problem += minimize_moves_objective(placement_vars)

    for constraint in lights_out_constraints(placement_vars, initial_board=board):
        problem += constraint

    problem.solve()
    if LpStatus[problem.status] != "Optimal":
        return None

    return get_solution(placement_vars)


if __name__ == "__main__":

    m, n = 25, 25
    initial_board = generate_board(m, n, 112)
    print_board(initial_board)

    solution = solve(initial_board)
    if not solution:
        print("This board is unsolvable.")

    works = apply_solution(initial_board, solution)

    print_board(initial_board)

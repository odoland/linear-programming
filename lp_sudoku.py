from pulp import *

prob = LpProblem("Sudoku", const.LpMinimize)

# Constraints
grid_vars = [[[0 for _ in range(9)] for _ in range(9)] for _ in range(9)]

for r in range(9):
    for c in range(9):
        for v in range(9):
            grid_vars[r][c][v] = LpVariable(f"{r},{c},{v}", cat=LpBinary)

# We can only have 1 value per cell
for r in range(9):
    for c in range(9):
        prob += lpSum([grid_vars[r][c][v] for v in range(9)]) == 1, f"val_{r}{c}"

# 1 of each per row
for r in range(9):
    for v in range(9):
        prob += lpSum([grid_vars[r][c][v] for c in range(9)]) == 1

# 1 of each per  col
for c in range(9):
    for v in range(9):
        prob += lpSum([grid_vars[r][c][v] for r in range(9)]) == 1

# 1 of each per box
box = []
for i in range(3):
    for j in range(3):
        box.append([i, j])

for v in range(9):
    for i in range(3):
        for j in range(3):
            print("box", i, j, ":", [(3 * i + dy, 3 * j + dx) for dy, dx in box])
            prob += (
                lpSum([grid_vars[3 * i + dy][3 * j + dx][v] for (dy, dx) in box]) == 1
            )


# The starting numbers are entered as constraints
input_data = [
    (5, 1, 1),
    (6, 2, 1),
    (8, 4, 1),
    (4, 5, 1),
    (7, 6, 1),
    (3, 1, 2),
    (9, 3, 2),
    (6, 7, 2),
    (8, 3, 3),
    (1, 2, 4),
    (8, 5, 4),
    (4, 8, 4),
    (7, 1, 5),
    (9, 2, 5),
    (6, 4, 5),
    (2, 6, 5),
    (1, 8, 5),
    (8, 9, 5),
    (5, 2, 6),
    (3, 5, 6),
    (9, 8, 6),
    (2, 7, 7),
    (6, 3, 8),
    (8, 7, 8),
    (7, 9, 8),
    (3, 4, 9),
    (1, 5, 9),
    (6, 6, 9),
    (5, 8, 9),
]

for (v, r, c) in input_data:
    prob += grid_vars[r - 1][c - 1][v - 1] == 1


prob.solve()
print("Status:", LpStatus[prob.status])

board = [[None for i in range(9)] for j in range(9)]

for i in range(9):
    for j in range(9):
        v = None
        for k in range(9):
            if grid_vars[i][j][k].value() == 1:
                if v is not None:
                    print("error")
                else:
                    v = k
                    board[i][j] = k + 1

for row in board:
    for col in row:
        print(col, end=" ")
    print()

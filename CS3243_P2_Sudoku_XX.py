import sys
import copy
import heapq
from collections import defaultdict
import time

class Cell(object):
    def __init__(self, coords, board):
        self.coords = coords
        self.board = board
        self.domain = self.initDomain()

    def initDomain(self):
        if self.board[self.coords[0]][self.coords[1]] != 0:
            return set([self.board[self.coords[0]][self.coords[1]]])
        dom = set()
        for i in range(1, 10):
            dom.add(i)
        for i in range(9):
            if i != self.coords[0] and self.board[i][self.coords[1]] != 0 and self.board[i][self.coords[1]] in dom:
                dom.remove(self.board[i][self.coords[1]])
            if i != self.coords[1] and self.board[self.coords[0]][i] != 0 and self.board[self.coords[0]][i] in dom:
                dom.remove(self.board[self.coords[0]][i])
        x0, y0 = (self.coords[1]//3) * 3, (self.coords[0]//3) * 3
        for i in range(3):
            for j in range(3):
                if not (x0+j == self.coords[1] and y0+i == self.coords[0]) and self.board[y0+i][x0+j] != 0 and self.board[y0+i][x0+j] in dom:
                    dom.remove(self.board[y0+i][x0+j])
        return dom

    @property
    def neighbors(self):
        neighbors = set()
        for i in range(9):
            if i != self.coords[0] and self.board[i][self.coords[1]] == 0:
                neighbors.add((i, self.coords[1]))
            if i != self.coords[1] and self.board[self.coords[0]][i] == 0:
                neighbors.add((self.coords[0], i))
        x0, y0 = (self.coords[1]//3) * 3, (self.coords[0]//3) * 3
        for i in range(3):
            for j in range(3):
                if not (x0+j == self.coords[1] and y0+i == self.coords[0]) and self.board[y0+i][x0+j] == 0:
                    neighbors.add((y0+i, x0+j))
        return neighbors

    def __str__(self):
        return str(self.board[self.coords[0]][self.coords[1]]) + ', ' + str(self.coords) + ', ' + str(self.domain) + ', ' + str(self.neighbors)

    @property
    def remainingValues(self):
        return len(self.domain)

    @property
    def degree(self):
        return len(self.neighbors)

class Sudoku(object):
    def __init__(self, puzzle):
        self.puzzle = puzzle # self.puzzle is a list of lists
        self.grid = self.initGrid()

    def initGrid(self):
        grid = [[None for _ in range(9)] for _ in range(9)]
        for y in range(9):
            for x in range(9):
                grid[y][x] = Cell((y, x), self.puzzle)
        return grid

    def isSolved(self):
        for i in range(9):
            for j in range(9):
                if self.puzzle[i][j] == 0:
                    return False
        return True

    def revise(self, cell, neigh, changes):
        revised = False
        if len(neigh.domain) != 1:
            return False
        for val in neigh.domain:
            if val in cell.domain:
                cell.domain.remove(val)
                changes.append((cell.coords, val))
                revised = True
        return revised

    def infer(self, changes, cell):
        q = []
        y, x = cell[0], cell[1]
        for i, j in self.grid[y][x].neighbors:
            if len(self.grid[i][j].domain) == 1:
                q.append((self.grid[y][x], self.grid[i][j]))
        while q:
            cell, neigh = q.pop()
            if self.revise(cell, neigh, changes):
                if len(cell.domain) == 0:
                    return False
                if len(cell.domain) == 1:
                    for i, j in cell.neighbors:
                        if (i, j) != neigh.coords:
                            q.append((self.grid[i][j], cell))
        return True

    def unassign(self, changes, cell, val):
        self.puzzle[cell.coords[0]][cell.coords[1]] = 0
        for change in changes:
            (y, x), val = change[0], change[1]
            self.grid[y][x].domain.add(val)

    def choose_cell_to_assign(self):
        min_domain = 10
        max_degree = -1
        chosen_row = None
        chosen_col = None
        for row in range(9):
            for col in range(9):
                if self.puzzle[row][col] == 0:
                    domain_size = len(self.grid[row][col].domain)
                    if domain_size < min_domain:
                        min_domain = domain_size
                        chosen_row = row
                        chosen_col = col
                    elif domain_size == min_domain:
                        degree = len(self.grid[row][col].neighbors)
                        if degree > max_degree:
                            max_degree = degree
                            chosen_row = row
                            chosen_col = col
        return self.grid[chosen_row][chosen_col]

    def least_constraining_values(self, cell):
        vals = {}
        for val in cell.domain:
            vals[val] = 0
            for i, j in cell.neighbors:
                if val in self.grid[i][j].domain:
                    vals[val] += 1
        x = sorted(vals.items(), key=lambda i: i[1])
        res = []
        for i in x:
            res.append(i[0])
        return res

    def backtrack(self):
        if self.isSolved():
            return True
        cell = self.choose_cell_to_assign()
        for val in self.least_constraining_values(cell):
            changes = []
            self.puzzle[cell.coords[0]][cell.coords[1]] = val
            for y, x in cell.neighbors:
                if val in self.grid[y][x].domain:
                    self.grid[y][x].domain.remove(val)
                    changes.append(((y,x), val))
            inferenceResult = self.infer(changes, cell.coords)
            if inferenceResult == True:
                res = self.backtrack()
                if res == True:
                    return True
            self.unassign(changes, cell, val) 
        return False

    def solve(self):
        start = time.time()
        self.backtrack()
        print("--- %s seconds ---" % (time.time() - start))
        return self.puzzle


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print ("\nUsage: python CS3243_P2_Sudoku_XX.py input.txt output.txt\n")
        raise ValueError("Wrong number of arguments!")

    try:
        f = open(sys.argv[1], 'r')
    except IOError:
        print ("\nUsage: python CS3243_P2_Sudoku_XX.py input.txt output.txt\n")
        raise IOError("Input file not found!")

    puzzle = [[0 for i in range(9)] for j in range(9)]
    lines = f.readlines()

    i, j = 0, 0
    for line in lines:
        for number in line:
            if '0' <= number <= '9':
                puzzle[i][j] = int(number)
                j += 1
                if j == 9:
                    i += 1
                    j = 0

    sudoku = Sudoku(puzzle)
    ans = sudoku.solve()

    with open(sys.argv[2], 'a') as f:
        for i in range(9):
            for j in range(9):
                f.write(str(ans[i][j]) + " ")
            f.write("\n")

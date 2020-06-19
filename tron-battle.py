import sys
from asyncio import Queue
from time import perf_counter_ns

FREE = "·"
WALL = "█"

PLAYERS_SYMBOLS = ["o", "+", "x", "¤"]
HEAD_SYMBOL = "■"
DEAD = -1, -1


class Game:
    def __str__(self):
        representation = ""
        for row in range(self.height):
            for col in range(self.width):
                representation += HEAD_SYMBOL if (row, col) in self.players else self.cell(row, col)
            representation += "\n"
        return representation

    def __repr__(self):
        return self.__str__()

    def __init__(self, width, height, players_starting_positions, current_player):
        self.width = width
        self.height = height
        self.nodes = [[FREE for _ in range(width)] for _ in range(height)]
        self.players = players_starting_positions
        for player, position in enumerate(players_starting_positions):
            self.update(player, *position)
        self.me = current_player

    def cell(self, row, col):
        if row < 0:
            return WALL
        if row >= self.height:
            return WALL
        if col < 0:
            return WALL
        if col >= self.width:
            return WALL

        return self.nodes[row][col]

    def neighbors(self, row, col):
        if row < 0:
            return []
        if row > self.height:
            return []
        if col < 0:
            return []
        if col > self.width:
            return []

        directions = [
            ("RIGHT", 0, 1),
            ("DOWN", 1, 0),
            ("LEFT", 0, -1),
            ("UP", -1, 0)
        ]
        return [(direction, row + diff_row, col + diff_col) for direction, diff_row, diff_col in directions]

    def free_neighbors(self, row, col):
        neighbors = self.neighbors(row, col)
        free = [neighbor for neighbor in neighbors if self.is_free(neighbor[1], neighbor[2])]
        return free

    def is_free(self, row, col):
        cell = self.cell(row, col)
        return cell != WALL and (cell == FREE or self.players[PLAYERS_SYMBOLS.index(cell)] == DEAD)

    def update(self, player, row, col):
        last_row, last_col = self.players[player]
        last_content = self.nodes[row][col]

        if row < 0 or col < 0:
            self.players[player] = DEAD
        else:
            self.players[player] = row, col
            self.nodes[row][col] = PLAYERS_SYMBOLS[player]

        return last_row, last_col, last_content

    def rollback(self, player, row, col, cell):
        self.players[player] = row, col
        self.nodes[row][col] = cell

    def alphabeta(self, player, depth, timer, alpha, beta):
        current_cell = self.players[player]
        possible_moves = self.free_neighbors(*current_cell)
        next_player = (player + 1) % len(self.players)

        if depth <= 0 or perf_counter_ns() - timer > 95000:
            valuation = self.valuation()
            return valuation, "TOO DEEP"

        if not possible_moves:
            last_row, last_col, last_content = self.update(player, -1, -1)
            move_value, _ = self.alphabeta(next_player, depth - 1, timer, alpha, beta)
            self.rollback(player, last_row, last_col, last_content)
            return move_value, "DEAD PERSON"

        maximising = player == self.me
        if maximising:
            value = -2
            best_direction = "GIVE UP"
            for direction, row, col in possible_moves:

                last_row, last_col, last_content = self.update(player, row, col)
                move_value, _ = self.alphabeta(next_player, depth - len(possible_moves), timer, alpha, beta)
                self.rollback(player, last_row, last_col, last_content)

                if move_value > value:
                    value = move_value
                    alpha = move_value
                    best_direction = direction
                if alpha > beta:
                    break
        else:
            value = 2
            best_direction = "GIVE UP"
            for direction, row, col in possible_moves:

                last_row, last_col, last_content = self.update(player, row, col)
                move_value, _ = self.alphabeta(next_player, depth - 1, timer, alpha, beta)
                self.rollback(player, last_row, last_col, last_content)

                if move_value < value:
                    value = move_value
                    beta = move_value
                    best_direction = direction
                if alpha > beta:
                    break
        return value, best_direction

    def valuation(self):
        my_value = 0
        enemy_value = 0
        queues = list()
        positions = list(filter(lambda player: player != DEAD, self.players))

        saved_nodes = [[content for content in row] for row in self.nodes]

        for cell in positions:
            queue = Queue()
            queue.put_nowait(cell)
            queues.append(queue)

        while not all(map(lambda queue: queue.empty(), queues)):
            for player, queue in enumerate(queues):
                if queue.empty():
                    continue
                if self.players[player][0] == -1:
                    item_row, item_col = queue.get_nowait()
                    self.nodes[item_row][item_col] = FREE
                    continue
                symbol = PLAYERS_SYMBOLS[player]
                item_row, item_col = queue.get_nowait()
                for _, neighbor_row, neighbor_col in self.free_neighbors(item_row, item_col):
                    self.nodes[neighbor_row][neighbor_col] = symbol

                    queue.put_nowait((neighbor_row, neighbor_col))
                    if player == self.me:
                        my_value += 1
                    else:
                        enemy_value += 1

        self.nodes = saved_nodes
        return (my_value - enemy_value) / (my_value + enemy_value + 1)

    def running(self):
        return any(map(lambda player: player[0] > 0, self.players))


def parse_input():
    while True:
        nb_players, player_index = [int(i) for i in input().split()]
        for player in range(nb_players):
            _, _, col, row = [int(i) for i in input().split()]
            print((player, row, col), file=sys.stderr)
            yield player, row, col


nb_players, player_index = [int(i) for i in input().split()]
players = []
for player in range(nb_players):
    col, row, _, _ = [int(i) for i in input().split()]
    players.append((row, col))

game = Game(30, 20, players, player_index)

inputs = parse_input()
while True:
    value, direction = game.alphabeta(player_index, 25, perf_counter_ns(), -2, 2)
    print(direction)
    for player in range(nb_players):
        game.update(*next(inputs))
    print(game, file=sys.stderr)
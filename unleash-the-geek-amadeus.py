import random
import sys
from collections import defaultdict

width, height = [int(i) for i in input().split()]

NONE = -1
ROBOT_ALLY = 0
ROBOT_ENEMY = 1
HOLE = 1
RADAR = 2
TRAP = 3
AMADEUSIUM = 4


class Pos:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def distance(self, pos):
        return abs(self.x - pos.x) + abs(self.y - pos.y)


class Entity(Pos):
    def __init__(self, x, y, type, id):
        super().__init__(x, y)
        self.type = type
        self.id = id


class Robot(Entity):
    def __init__(self, x, y, type, id, item):
        super().__init__(x, y, type, id)
        self.item = item

    def is_dead(self):
        return self.x == -1 and self.y == -1

    def move(self, x, y, message=""):
        print(f"MOVE {x} {y} {message}")

    def wait(self, message=""):
        print(f"WAIT {message}")

    def dig(self, x, y, message=""):
        print(f"DIG {x} {y} {message}")

    def request(self, requested_item, message=""):
        if requested_item == RADAR:
            print(f"REQUEST RADAR {message}")
        elif requested_item == TRAP:
            print(f"REQUEST TRAP {message}")
        else:
            raise Exception(f"Unknown item {requested_item}")


class Cell(Pos):
    def __init__(self, x, y, amadeusium, hole):
        super().__init__(x, y)
        self.amadeusium = amadeusium
        self.hole = hole
        self.potential_trap = False

    def has_hole(self):
        return self.hole == HOLE

    def update(self, amadeusium, hole):
        self.amadeusium = amadeusium
        self.hole = hole


class Grid:
    def __init__(self):
        self.cells = []
        for y in range(height):
            for x in range(width):
                self.cells.append(Cell(x, y, 0, 0))

    def get_cell(self, x, y):
        if width > x >= 0 and height > y >= 0:
            return self.cells[x + width * y]
        return Cell(x, y, 0, 0)


my_trap_spots = list(range(2, height - 2))

class Game:
    def update_entity(self, id, type, x, y, item):
        print("update_entity", file=sys.stderr)
        if type == ROBOT_ALLY:
            self.my_robots.append(Robot(x, y, type, id, item))
        elif type == ROBOT_ENEMY:
            current = Robot(x, y, type, id, item)
            if self.enemy_history[id]:
                previous = self.enemy_history[id][0]
                if previous.x == current.x and previous.y == current.y:
                    self.grid.get_cell(current.x, current.y).potential_trap = True
                    self.grid.get_cell(current.x + 1, current.y).potential_trap = True
                    self.grid.get_cell(current.x, current.y + 1).potential_trap = True
                    self.grid.get_cell(current.x - 1, current.y).potential_trap = True
                    self.grid.get_cell(current.x, current.y + 1).potential_trap = True
            self.enemy_history[id].insert(0, current)
        elif type == TRAP:
            self.traps.append(Entity(x, y, type, id))
        elif type == RADAR:
            self.radars.append(Entity(x, y, type, id))

    def __init__(self, turns):
        self.turns_left = turns
        self.grid = Grid()
        self.my_score = 0
        self.enemy_score = 0
        self.radar_cooldown = 0
        self.trap_cooldown = 0
        self.radars = []
        self.traps = []
        self.my_robots = []
        self.seeking_radar = False
        self.seeking_trap = False
        self.awaiting_trap = False
        self.enemy_history = defaultdict(lambda: list())

    def first_radar_spot(self):
        for n in range(5, width-2):
            for m in range(2, height-2):
                cell = self.grid.get_cell(n, m)
                radar_distances = list(map(lambda radar: cell.distance(radar), self.radars))
                if not radar_distances:
                    return cell
                elif min(radar_distances) > 5:
                    return cell
        return None

    def first_trap_spot(self):
        for n in my_trap_spots:
            if not self.is_trap(self.grid.get_cell(1, n)):
                return Pos(1, n)
        return None

    def is_trap(self, cell):
        return (cell.x, cell.y) in map(lambda trap: (trap.x, trap.y), self.traps)

    def ratio_mine_vs_them_is_over(self, ratio):
        enemy_robots_in_range = 0
        my_robots_in_range = 0

        for robot in [value[0] for value in self.enemy_history.values()]:
            for trap in self.traps:
                if robot.distance(trap) < 2:
                    enemy_robots_in_range += 1
                    break

        for robot in self.my_robots:
            for trap in self.traps:
                if robot.distance(trap) < 2:
                    my_robots_in_range += 1
                    break

        if my_robots_in_range == 0:
            return False
        else:
            return enemy_robots_in_range / my_robots_in_range >= ratio

    def near_trap(self, cell):
        if not self.traps:
            return None
        trap_distances = list(map(lambda trap: trap.distance(cell), self.traps))
        return self.traps[trap_distances.index(min(trap_distances))]

    def winning(self):
        # return True
        bot_valuation = lambda robot: 0 if robot.is_dead() else 1
        nb_my_robots = sum(map(bot_valuation, self.my_robots))
        nb_enemy_robots = sum(map(bot_valuation, [value[0] for value in self.enemy_history.values()]))
        if not nb_my_robots:
            return False
        return (self.my_score + (nb_my_robots * self.turns_left / 10)) - (self.enemy_score + (nb_enemy_robots * self.turns_left / 10)) > (self.turns_left / 20)

    def nearest_amadeusium_spot(self, position):
        safe_amadeusium_spots_distances = list(map(lambda spot: position.distance(spot), self.safe_amadeusium_spots))
        unsafe_amadeusium_spots_distances = list(map(lambda spot: position.distance(spot), self.unsafe_amadeusium_spots))
        if safe_amadeusium_spots_distances:
            return self.safe_amadeusium_spots[safe_amadeusium_spots_distances.index(min(safe_amadeusium_spots_distances))]
        elif unsafe_amadeusium_spots_distances:
            return self.unsafe_amadeusium_spots[unsafe_amadeusium_spots_distances.index(min(unsafe_amadeusium_spots_distances))]
        else:
            return None

    def near_HQ(self, robot):
        return robot.x == min(map(lambda robot: robot.x, filter(lambda robot: not robot.is_dead(), self.my_robots)))

    def next_turn(self):
        print("next_turn", file=sys.stderr)
        self.radars = []
        self.traps = []
        self.my_robots = []

        self.seeking_radar = False
        self.seeking_trap = False
        self.awaiting_trap = False

        self.turns_left -= 1

        cells = [self.grid.get_cell(n, m) for n in range(width) for m in range(height)]
        amadeusium_spots = list(filter(lambda cell: cell.amadeusium != "?" and int(cell.amadeusium) > 0 , cells))
        self.safe_amadeusium_spots = list(filter(lambda cell: not cell.potential_trap, amadeusium_spots))
        self.unsafe_amadeusium_spots = list(filter(lambda cell: cell.potential_trap, amadeusium_spots))
        print("next_turn end", file=sys.stderr)


def apply_strategy(game, robot):
    print("apply_strategy", file=sys.stderr)
    if robot.is_dead():
        robot.wait("Dead!")
        return

    next_cell = game.grid.get_cell(robot.x + 1, robot.y)
    radar_spot = game.first_radar_spot()
    trap_spot = game.first_trap_spot()
    near_trap = game.near_trap(robot)
    winning = game.winning()
    amadeusium_spot = game.nearest_amadeusium_spot(robot)
    near_HQ = game.near_HQ(robot)
    if robot.item == AMADEUSIUM:
        robot.move(0, robot.y)
    elif not trap_spot \
            and not game.awaiting_trap \
            and game.ratio_mine_vs_them_is_over(1 if winning else 2) \
            and robot.distance(near_trap) < 2:
        robot.dig(near_trap.x, near_trap.y, "EXPLODE")
        game.awaiting_trap = True
    elif robot.item == RADAR and radar_spot:
        robot.dig(radar_spot.x + robot.id % 2, radar_spot.y + robot.id // 2 % 2)
    elif robot.item == TRAP and trap_spot:
        robot.dig(trap_spot.x, trap_spot.y)

    elif radar_spot and game.radar_cooldown == 0 and not game.seeking_radar and robot.item == NONE and near_HQ:
        robot.request(RADAR, "Request Radar")
        game.seeking_radar = True
    elif not winning and trap_spot and game.trap_cooldown == 0 and not game.seeking_trap and robot.item == NONE and near_HQ:
        robot.request(TRAP, "Request Trap")
        game.seeking_trap = True
    elif not winning and not trap_spot and not game.awaiting_trap and near_trap and robot.distance(near_trap) > 1:
        robot.move(near_trap.x - 1, near_trap.y, "Approach trap")
        game.awaiting_trap = True
    elif near_trap and robot.distance(near_trap) <= 1 and not game.awaiting_trap and not game.ratio_mine_vs_them_is_over(1 if winning else 2):
        robot.wait("Waiting for enemies")
        game.awaiting_trap = True
    elif amadeusium_spot:
        robot.dig(amadeusium_spot.x, amadeusium_spot.y, "Targeted digging")
    elif next_cell and not next_cell.has_hole():
        robot.dig(robot.x + 1, robot.y, "Blind digging")
    else:
        robot.wait("Lost")


game = Game(200)

while True:
    print("main_loop", file=sys.stderr)
    game.my_score, game.enemy_score = [int(i) for i in input().split()]
    for i in range(height):
        inputs = input().split()
        for j in range(width):
            amadeusium = inputs[2 * j]
            hole = int(inputs[2 * j + 1])
            game.grid.get_cell(j, i).update(amadeusium, hole)
    entity_count, game.radar_cooldown, game.trap_cooldown = [int(i) for i in input().split()]
    game.next_turn()
    for i in range(entity_count):
        id, type, x, y, item = [int(j) for j in input().split()]
        game.update_entity(id, type, x, y, item)

    for robot in game.my_robots:
        print("robot_loop", file=sys.stderr)
        apply_strategy(game, robot)

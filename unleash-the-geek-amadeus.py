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

    def __str__(self):
        return str((self.x, self.y))


class Entity(Pos):
    def __init__(self, x, y, type, id):
        super().__init__(x, y)
        self.type = type
        self.id = id

    def __str__(self):
        return "{}:[{},{}]".format(self.id, self.type, super().__str__())

    def __repr__(self):
        return "{}:[{},{}]".format(self.id, self.type, super().__str__())


class Robot(Entity):
    def __init__(self, x, y, type, id, item):
        super().__init__(x, y, type, id)
        self.item = item

    def is_dead(self):
        return self.x == -1 and self.y == -1

    def move(self, x, y, message=""):
        print(f"MOVE {x} {y} {message}")

    def move_vec(self, vector, message=""):
        self.move(self.x + vector[0], self.y + vector[1], message)

    def wait(self, message=""):
        print(f"WAIT {message}")

    def dig(self, x, y, message=""):
        print(f"DIG {x} {y} {message}")

    def dig_vec(self, vector, message=""):
        self.dig(self.x + vector[0], self.y + vector[1], message)

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
        self._potential_trap = False

    def set_potential_trap(self):
        if self.hole:
            self._potential_trap = True

    def has_hole(self):
        return self.hole == HOLE

    def update(self, amadeusium, hole):
        self.amadeusium = amadeusium
        self.hole = hole

    def __str__(self):
        return "cell:[{},{},{}]".format(self.amadeusium, self.hole, super().__str__())

    def __repr__(self):
        return "cell:[{},{},{}]".format(self.amadeusium, self.hole, super().__str__())

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


class Game:
    def update_entity(self, id, type, x, y, item):
        entity = Entity(x, y, type, id)
        if type == ROBOT_ALLY:
            self.my_robots.append(Robot(x, y, type, id, item))
        elif type == ROBOT_ENEMY:
            current = Robot(x, y, type, id, item)
            if self.enemy_history[id]:
                previous = self.enemy_history[id][0]
                if previous.x == current.x and previous.y == current.y:
                    self.grid.get_cell(current.x, current.y).set_potential_trap()
                    self.grid.get_cell(current.x + 1, current.y).set_potential_trap()
                    self.grid.get_cell(current.x, current.y + 1).set_potential_trap()
                    self.grid.get_cell(current.x - 1, current.y).set_potential_trap()
                    self.grid.get_cell(current.x, current.y + 1).set_potential_trap()
            self.enemy_history[id].insert(0, current)
        elif type == TRAP:
            print(entity, file=sys.stderr)
            self.traps.append(entity)
        elif type == RADAR:
            self.radars.append(entity)

    def __init__(self):
        self.turn = 0
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
            for m in range(3, height-3):
                cell = self.grid.get_cell(n, m)
                if self.is_trap(cell):
                    continue
                if cell._potential_trap:
                    continue
                radar_distances = list(map(lambda radar: cell.distance(radar), self.radars))
                if not radar_distances:
                    return cell
                elif min(radar_distances) > 6:
                    return cell
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

    def near_traps(self, cell, distance=1):
        if not self.traps:
            return []
        near_traps = list(filter(lambda trap: trap.distance(cell) <= distance, self.traps))
        return near_traps

    def winning(self):
        bot_valuation = lambda robot: 0 if robot.is_dead() else 1
        nb_my_robots = sum(map(bot_valuation, self.my_robots))
        nb_enemy_robots = sum(map(bot_valuation, self.enemy_robots()))
        if not nb_my_robots:
            return False
        return (self.my_score + (nb_my_robots * 2)) > (self.enemy_score + (nb_enemy_robots * 2) + 10)

    def nearest_amadeusium_spot(self, position):
        print(self.safe_amadeusium_spots, file=sys.stderr)
        print(self.unsafe_amadeusium_spots, file=sys.stderr)
        safe_amadeusium_spots_distances = list(map(lambda spot: position.distance(spot), self.safe_amadeusium_spots))
        unsafe_amadeusium_spots_distances = list(map(lambda spot: position.distance(spot), self.unsafe_amadeusium_spots))

        spots = [None, None]
        if safe_amadeusium_spots_distances:
            spots[0] = self.safe_amadeusium_spots[safe_amadeusium_spots_distances.index(min(safe_amadeusium_spots_distances))]

        if unsafe_amadeusium_spots_distances:
            spots[1] = self.unsafe_amadeusium_spots[unsafe_amadeusium_spots_distances.index(min(unsafe_amadeusium_spots_distances))]

        return spots

    def near_HQ(self, robot):
        return robot.x == min(map(lambda robot: robot.x, filter(lambda robot: not robot.is_dead(), self.my_robots)))

    def enemy_robots(self):
        return [value[0] for value in self.enemy_history.values()]

    def next_turn(self):
        self.radars = []
        self.traps = []
        self.my_robots = []

        self.seeking_radar = False
        self.seeking_trap = False
        self.awaiting_trap = False

        self.turn += 1

    def compute_strat(self):
        cells = [self.grid.get_cell(n, m) for n in range(width) for m in range(height)]
        amadeusium_spots = list(
            filter(lambda cell: cell.amadeusium != "?" and int(cell.amadeusium) > 0 and not self.is_trap(cell), cells))
        self.safe_amadeusium_spots = list(filter(lambda cell: not cell._potential_trap, amadeusium_spots))
        self.unsafe_amadeusium_spots = list(filter(lambda cell: cell._potential_trap, amadeusium_spots))
        print("traps " + str(self.traps), file=sys.stderr)
        print("next turn " + str(amadeusium_spots), file=sys.stderr)
        print("next turn " + str(self.safe_amadeusium_spots), file=sys.stderr)
        print("next turn " + str(self.unsafe_amadeusium_spots), file=sys.stderr)



def apply_strategy(game, robot):
    if robot.is_dead():
        robot.wait("Dead!")
        return

    ending = game.turn > 122
    beginning = game.turn < 66

    winning = game.winning()
    safe_amadeusium, unsafe_amadeusium = game.nearest_amadeusium_spot(robot)
    safe_amadeusium, unsafe_amadeusium = safe_amadeusium, None if beginning else unsafe_amadeusium
    if safe_amadeusium:
        game.safe_amadeusium_spots.remove(safe_amadeusium)
    if unsafe_amadeusium:
        game.unsafe_amadeusium_spots.remove(unsafe_amadeusium)
    radar_spot = game.first_radar_spot() or safe_amadeusium or unsafe_amadeusium
    amadeusium = safe_amadeusium or unsafe_amadeusium
    near_HQ = game.near_HQ(robot)
    near_traps = game.near_traps(robot)
    opportunity_trap = find_opportunity_trap(game, near_traps, robot, unsafe_amadeusium)


    if robot.item == AMADEUSIUM:
        robot.move(0, robot.y, "Back to HQ")
    elif opportunity_trap:
        robot.dig(opportunity_trap.x, opportunity_trap.y, "Opportunity")
    elif robot.item == RADAR and radar_spot and len(game.safe_amadeusium_spots) < 5:
        robot.dig(radar_spot.x, radar_spot.y, "Put Standard Radar")
    elif robot.item == RADAR and amadeusium and len(game.safe_amadeusium_spots) >= 5:
        robot.dig(amadeusium.x, amadeusium.y, "Put Radar Wherever")
    elif robot.item == TRAP and amadeusium:
        robot.dig(amadeusium.x, amadeusium.y, "Put Trap on Amadeusium")
    elif radar_spot and game.radar_cooldown == 0 and not game.seeking_radar and robot.item == NONE and near_HQ and len(game.safe_amadeusium_spots) < 8:
        robot.request(RADAR, "Request Radar")
        game.seeking_radar = True
    elif game.radar_cooldown == 0 and not game.seeking_radar and robot.x == 0 and len(game.safe_amadeusium_spots) >= 5:
        robot.request(RADAR, "Request Radar")
        game.seeking_radar = True
    elif not ending and not winning and safe_amadeusium and game.trap_cooldown == 0 and not game.seeking_trap and robot.item == NONE and robot.x == 0:
        robot.request(TRAP, "Request Trap")
        game.seeking_trap = True
    elif amadeusium:
        robot.dig(amadeusium.x, amadeusium.y, "Safish Dig")
    else:
        robot.wait("...")


def find_opportunity_trap(game, near_traps, robot, unsafe_amadeusium):
    opportunity_trap = None
    opportunity_trap_value = 0
    for trap in near_traps:
        enemy_value = len(list(filter(lambda robot: robot.distance(trap) <= 1, game.enemy_robots())))
        my_value = len(list(filter(lambda robot: robot.distance(trap) <= 1, game.my_robots)))
        if (enemy_value - my_value) > opportunity_trap_value:
            opportunity_trap = trap
            opportunity_trap_value = enemy_value - my_value
    if unsafe_amadeusium and robot.distance(unsafe_amadeusium) <= 1:
        enemy_value = len(list(filter(lambda robot: robot.distance(unsafe_amadeusium) <= 1, game.enemy_robots())))
        my_value = len(list(filter(lambda robot: robot.distance(unsafe_amadeusium) <= 1, game.my_robots)))
        if (enemy_value - my_value) > opportunity_trap_value:
            opportunity_trap = unsafe_amadeusium
    return opportunity_trap


game = Game()

while True:
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
    game.compute_strat()

    if game.turn == 1:
        random.shuffle(game.my_robots)
        game.my_robots[0].request(RADAR)
        game.my_robots[1].request(TRAP)
        game.my_robots[2].wait()
        game.my_robots[3].wait()
        game.my_robots[4].wait()
    elif game.turn == 2:
        game.my_robots[0].move_vec((+4, 0))
        game.my_robots[1].move_vec((+4, 0))
        game.my_robots[2].move_vec((+4, 0))
        game.my_robots[3].move_vec((+4, 0))
        game.my_robots[4].move_vec((+4, 0))
    elif game.turn == 3:
        game.my_robots[0].dig_vec((+1, 0))
        game.my_robots[1].dig_vec((+1, 0))
        game.my_robots[2].dig_vec((+1, 0))
        game.my_robots[3].dig_vec((+1, 0))
        game.my_robots[4].dig_vec((+1, 0))
    elif game.turn == 4:
        game.my_robots[0].move_vec((-4, 0))
        game.my_robots[1].move_vec((-4, 0))
        game.my_robots[2].move_vec((-4, 0))
        game.my_robots[3].move_vec((-4, 0))
        game.my_robots[4].move_vec((-4, 0))
    else:
        for robot in game.my_robots:
            apply_strategy(game, robot)

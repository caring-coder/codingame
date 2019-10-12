import sys


class Pos:
    def __init__(self, x, y):
        self.x = x
        self.y = y


room_length = int(input())
lighting_length = int(input())

candles = []
for row in range(room_length):
    for col, value in enumerate(input().split()):
        if value == "C":
            candles.append(Pos(row, col))


def distance(pos1, pos2):
    return max(abs(pos1.x - pos2.x), abs(pos1.y - pos2.y))


nb = 0
for i in range(room_length * room_length):
    cell = Pos(i // room_length, i % room_length)
    distance_to_candles = map(lambda candle: distance(cell, candle), candles)
    far_from_candles = map(lambda dist: dist >= lighting_length, distance_to_candles)
    nb += 1 if all(far_from_candles) else 0

print(nb)

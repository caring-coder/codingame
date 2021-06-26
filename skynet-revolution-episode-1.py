import sys


class Node:
    def __init__(self, index):
        self.index = index
        self.neighbors = set()
    
    def append(self, node):
        self.neighbors.add(node)
    
    def remove(self, node):
        self.neighbors.remove(node)
    
    def __str__(self):
        return "{}{}".format(self.index, [n.index for n in self.neighbors])
    
    def __repr__(self):
        return "{}{}".format(self.index,  [n.index for n in self.neighbors])
    
    def shortest_path_to(self, goals):
        queue = [(self, [self])]
        while queue:
            node, path = queue.pop(0)
            print("queue={} node={} path={} goals={}".format(queue, node, path, goals), file=sys.stderr)
            for neighbor in node.neighbors - set(path):
                if neighbor in goals:
                    yield path + [neighbor]
                else:
                    queue.append((neighbor, path + [neighbor]))


nb_nodes, nb_links, nb_exits = [int(i) for i in input().split()]

nodes = [Node(i) for i in range(nb_nodes)]
exits = []

for link_idx in range(nb_links):
    link_start, link_end = [int(value) for value in input().split()]
    nodes[link_start].append(nodes[link_end])
    nodes[link_end].append(nodes[link_start])

for exit_idx in range(nb_exits):
    exit_node = int(input())
    exits.append(nodes[exit_node])

for node in nodes:
    print(node, file=sys.stderr)

while True:
    skynet_agent_node = nodes[int(input())]
    exit_path = next(skynet_agent_node.shortest_path_to(exits))
    link_start, link_end = exit_path[0].index, exit_path[1].index
    print(exit_path, file=sys.stderr)
    print("{} {}".format(link_start, link_end))
    nodes[link_start].remove(nodes[link_end])
    nodes[link_end].remove(nodes[link_start])

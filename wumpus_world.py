import random
from collections import deque

class WumpusWorld:
    def __init__(self, grid_size=4):
        self.grid_size = grid_size
        self.agent_pos = (0, 0)  # Starting position (top-left)
        self.agent_dir = "right"  # Initial direction
        self.has_gold = False
        self.has_arrow = True
        self.wumpus_alive = True
        self.world = self.generate_world()
        self.visited = set([(0, 0)])
        self.safe_cells = set([(0, 0)])
        self.breezy_cells = set()
        self.stenchy_cells = set()
        self.knowledge_base = {}
        self.initialize_knowledge_base()
        self.percepts = self.get_percepts()

    def initialize_knowledge_base(self):
        """Initialize knowledge about each cell"""
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                self.knowledge_base[(i, j)] = {
                    "pit": "unknown",
                    "wumpus": "unknown",
                    "safe": False
                }
        # Starting cell is safe
        self.knowledge_base[(0, 0)]["safe"] = True

    def generate_world(self):
        """Generate random world with pits, Wumpus, and gold"""
        world = [[{"pit": False, "wumpus": False, "gold": False} 
                for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        
        # Place pits (20% chance per cell, except start)
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                if (i, j) != (0, 0) and random.random() < 0.2:
                    world[i][j]["pit"] = True
        
        # Place Wumpus (random, not at start)
        wumpus_pos = (random.randint(0, self.grid_size-1), 
                     random.randint(0, self.grid_size-1))
        while wumpus_pos == (0, 0):
            wumpus_pos = (random.randint(0, self.grid_size-1), 
                         random.randint(0, self.grid_size-1))
        world[wumpus_pos[0]][wumpus_pos[1]]["wumpus"] = True
        
        # Place gold (random, not at start)
        gold_pos = (random.randint(0, self.grid_size-1), 
                   random.randint(0, self.grid_size-1))
        while gold_pos == (0, 0):
            gold_pos = (random.randint(0, self.grid_size-1), 
                       random.randint(0, self.grid_size-1))
        world[gold_pos[0]][gold_pos[1]]["gold"] = True
        
        return world

    def get_percepts(self):
        """Get current percepts based on agent position"""
        x, y = self.agent_pos
        cell = self.world[x][y]
        percepts = {
            "stench": False,
            "breeze": False,
            "glitter": False,
            "bump": False,
            "scream": False
        }
        
        # Check adjacent cells for Wumpus (stench) and pits (breeze)
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.grid_size and 0 <= ny < self.grid_size:
                if self.world[nx][ny].get("wumpus", False) and self.wumpus_alive:
                    percepts["stench"] = True
                    self.stenchy_cells.add((x, y))
                if self.world[nx][ny]["pit"]:
                    percepts["breeze"] = True
                    self.breezy_cells.add((x, y))
        
        # Current cell percepts
        if cell["gold"]:
            percepts["glitter"] = True
        
        return percepts

    def move_forward(self):
        """Move agent forward based on current direction"""
        x, y = self.agent_pos
        new_x, new_y = x, y
        
        if self.agent_dir == "up":
            new_y -= 1
        elif self.agent_dir == "down":
            new_y += 1
        elif self.agent_dir == "left":
            new_x -= 1
        elif self.agent_dir == "right":
            new_x += 1
        
        # Check if move is valid
        if 0 <= new_x < self.grid_size and 0 <= new_y < self.grid_size:
            self.agent_pos = (new_x, new_y)
            self.visited.add((new_x, new_y))
            self.update_knowledge_base()
            self.percepts = self.get_percepts()
            return True
        else:
            self.percepts["bump"] = True
            return False

    def turn_left(self):
        """Turn agent 90 degrees left"""
        dirs = ["up", "left", "down", "right"]
        idx = dirs.index(self.agent_dir)
        self.agent_dir = dirs[(idx + 1) % 4]
        self.percepts = self.get_percepts()

    def turn_right(self):
        """Turn agent 90 degrees right"""
        dirs = ["up", "right", "down", "left"]
        idx = dirs.index(self.agent_dir)
        self.agent_dir = dirs[(idx + 1) % 4]
        self.percepts = self.get_percepts()

    def shoot_arrow(self):
        """Shoot arrow in current direction"""
        if not self.has_arrow:
            return False
        
        self.has_arrow = False
        x, y = self.agent_pos
        wumpus_killed = False
        
        # Arrow travels in current direction
        if self.agent_dir == "up":
            for i in range(y - 1, -1, -1):
                if self.world[x][i].get("wumpus", False):
                    wumpus_killed = True
                    self.world[x][i]["wumpus"] = False
                    break
        elif self.agent_dir == "down":
            for i in range(y + 1, self.grid_size):
                if self.world[x][i].get("wumpus", False):
                    wumpus_killed = True
                    self.world[x][i]["wumpus"] = False
                    break
        elif self.agent_dir == "left":
            for j in range(x - 1, -1, -1):
                if self.world[j][y].get("wumpus", False):
                    wumpus_killed = True
                    self.world[j][y]["wumpus"] = False
                    break
        elif self.agent_dir == "right":
            for j in range(x + 1, self.grid_size):
                if self.world[j][y].get("wumpus", False):
                    wumpus_killed = True
                    self.world[j][y]["wumpus"] = False
                    break
        
        if wumpus_killed:
            self.wumpus_alive = False
            self.percepts["scream"] = True
            # Update KB - all cells with stench are now safe
            for cell in self.stenchy_cells:
                self.knowledge_base[cell]["wumpus"] = False
                self.knowledge_base[cell]["safe"] = True
                self.safe_cells.add(cell)
            return True
        
        return False

    def grab_gold(self):
        """Grab gold if present in current cell"""
        x, y = self.agent_pos
        if self.world[x][y]["gold"]:
            self.has_gold = True
            self.world[x][y]["gold"] = False
            self.percepts["glitter"] = False
            return True
        return False

    def update_knowledge_base(self):
        """Update knowledge based on current percepts"""
        x, y = self.agent_pos
        
        # Current cell is safe
        self.knowledge_base[(x, y)]["safe"] = True
        self.knowledge_base[(x, y)]["pit"] = False
        self.knowledge_base[(x, y)]["wumpus"] = False
        self.safe_cells.add((x, y))
        
        # If no breeze, adjacent cells are pit-free
        if not self.percepts["breeze"]:
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.grid_size and 0 <= ny < self.grid_size:
                    self.knowledge_base[(nx, ny)]["pit"] = False
                    if self.knowledge_base[(nx, ny)]["wumpus"] == False:
                        self.knowledge_base[(nx, ny)]["safe"] = True
                        self.safe_cells.add((nx, ny))
        
        # If no stench, adjacent cells are wumpus-free
        if not self.percepts["stench"]:
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.grid_size and 0 <= ny < self.grid_size:
                    self.knowledge_base[(nx, ny)]["wumpus"] = False
                    if self.knowledge_base[(nx, ny)]["pit"] == False:
                        self.knowledge_base[(nx, ny)]["safe"] = True
                        self.safe_cells.add((nx, ny))
        
        # If breeze, at least one adjacent cell has a pit
        if self.percepts["breeze"]:
            adjacent_unknown = []
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.grid_size and 0 <= ny < self.grid_size:
                    if self.knowledge_base[(nx, ny)]["pit"] == "unknown":
                        adjacent_unknown.append((nx, ny))
            
            # If only one unknown adjacent cell, it must have a pit
            if len(adjacent_unknown) == 1:
                pit_cell = adjacent_unknown[0]
                self.knowledge_base[pit_cell]["pit"] = True
                self.knowledge_base[pit_cell]["safe"] = False
        
        # If stench, at least one adjacent cell has a wumpus
        if self.percepts["stench"] and self.wumpus_alive:
            adjacent_unknown = []
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.grid_size and 0 <= ny < self.grid_size:
                    if self.knowledge_base[(nx, ny)]["wumpus"] == "unknown":
                        adjacent_unknown.append((nx, ny))
            
            # If only one unknown adjacent cell, it must have a wumpus
            if len(adjacent_unknown) == 1:
                wumpus_cell = adjacent_unknown[0]
                self.knowledge_base[wumpus_cell]["wumpus"] = True
                self.knowledge_base[wumpus_cell]["safe"] = False

    def get_safe_move(self):
        """Find the next safe move using BFS"""
        x, y = self.agent_pos
        possible_moves = []
        
        # Check adjacent safe, unvisited cells first
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.grid_size and 0 <= ny < self.grid_size:
                if (nx, ny) in self.safe_cells and (nx, ny) not in self.visited:
                    possible_moves.append((nx, ny))
        
        if not possible_moves:
            # No adjacent safe moves, find nearest safe unvisited cell
            for safe_cell in self.safe_cells:
                if safe_cell not in self.visited:
                    path = self.find_path((x, y), safe_cell)
                    if path:
                        return path[1] if len(path) > 1 else path[0]
        
        return possible_moves[0] if possible_moves else None

    def find_path(self, start, goal):
        """BFS pathfinding avoiding unsafe cells"""
        queue = deque()
        queue.append([start])
        visited = set([start])
        
        while queue:
            path = queue.popleft()
            node = path[-1]
            
            if node == goal:
                return path
            
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = node[0] + dx, node[1] + dy
                if (0 <= nx < self.grid_size and 0 <= ny < self.grid_size and
                    (nx, ny) in self.safe_cells and (nx, ny) not in visited):
                    visited.add((nx, ny))
                    new_path = list(path)
                    new_path.append((nx, ny))
                    queue.append(new_path)
        
        return None

    def get_direction_to_move(self, target_pos):
        """Determine which turn/move is needed to reach target"""
        x, y = self.agent_pos
        tx, ty = target_pos
        
        if tx < x and self.agent_dir != "left":
            return "left"
        elif tx > x and self.agent_dir != "right":
            return "right"
        elif ty < y and self.agent_dir != "up":
            return "up"
        elif ty > y and self.agent_dir != "down":
            return "down"
        else:
            return "forward"

    def is_game_over(self):
        """Check if game is won or lost"""
        x, y = self.agent_pos
        cell = self.world[x][y]
        
        if cell["pit"] or (cell.get("wumpus", False) and self.wumpus_alive):
            return "lose"
        if self.has_gold and self.agent_pos == (0, 0):
            return "win"
        return "continue"
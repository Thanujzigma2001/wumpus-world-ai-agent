import random
import numpy as np
from collections import deque, defaultdict

class WumpusAgent:
    def __init__(self, world):
        self.world = world
        self.visited = set([(0, 0)])
        self.safe_cells = set([(0, 0)])
        self.planned_path = []
        self.knowledge_base = self._init_knowledge_base()
        self.action_history = []
        
        # Training and metrics
        self.metrics = {
            'cells_explored': 0,
            'safe_moves': 0,
            'risky_moves': 0,
            'gold_grabbed': 0,
            'wumpus_shots': 0,
            'total_reward': 0,
            'action_counts': defaultdict(int)
        }
        
        # Hyperparameters
        self.exploration_rate = 0.3
        self.conservatism = 0.5  # 0=risk neutral, 1=extremely cautious

    def _init_knowledge_base(self):
        kb = {}
        for x in range(self.world.grid_size):
            for y in range(self.world.grid_size):
                kb[(x, y)] = {
                    'pit_prob': 0.2 if (x,y) != (0,0) else 0.0,
                    'wumpus_prob': 0.0 if (x,y) == (0,0) else 1.0/(self.world.grid_size**2 - 1),
                    'visited': False
                }
        return kb

    def update_knowledge(self):
        x, y = self.world.agent_pos
        self.visited.add((x, y))
        self.safe_cells.add((x, y))
        self.knowledge_base[(x, y)]['visited'] = True
        self.knowledge_base[(x, y)]['pit_prob'] = 0.0
        self.knowledge_base[(x, y)]['wumpus_prob'] = 0.0

        # Update based on current percepts
        if not self.world.percepts['breeze']:
            self._mark_adjacent_pit_free(x, y)
        if not self.world.percepts['stench']:
            self._mark_adjacent_wumpus_free(x, y)
            
        # Update metrics
        self._update_metrics()

    def _mark_adjacent_pit_free(self, x, y):
        for dx, dy in [(0,1), (1,0), (0,-1), (-1,0)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.world.grid_size and 0 <= ny < self.world.grid_size:
                self.knowledge_base[(nx, ny)]['pit_prob'] = 0.0
                if self.knowledge_base[(nx, ny)]['wumpus_prob'] == 0:
                    self.safe_cells.add((nx, ny))

    def _mark_adjacent_wumpus_free(self, x, y):
        for dx, dy in [(0,1), (1,0), (0,-1), (-1,0)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.world.grid_size and 0 <= ny < self.world.grid_size:
                self.knowledge_base[(nx, ny)]['wumpus_prob'] = 0.0
                if self.knowledge_base[(nx, ny)]['pit_prob'] == 0:
                    self.safe_cells.add((nx, ny))

    def _update_metrics(self):
        x, y = self.world.agent_pos
        risk = self.knowledge_base[(x, y)]['pit_prob'] + self.knowledge_base[(x, y)]['wumpus_prob']
        
        if risk > 0.3:
            self.metrics['risky_moves'] += 1
        else:
            self.metrics['safe_moves'] += 1
            
        self.metrics['cells_explored'] = len(self.visited)
        self.metrics['total_reward'] -= 1  # Small penalty for each step

    def decide_action(self):
        x, y = self.world.agent_pos
        action = None
        
        # Priority 1: Grab gold if seen
        if self.world.percepts['glitter'] and not self.world.has_gold:
            action = 'grab'
            
        # Priority 2: Return home with gold
        elif self.world.has_gold:
            if (x, y) == (0, 0):
                action = 'climb'
            else:
                action = self._plan_path_home()
                
        # Priority 3: Shoot Wumpus if certain and aligned
        elif (self.world.has_arrow and 
              self.world.percepts['stench'] and 
              self._should_shoot()):
            action = 'shoot'
            
        # Priority 4: Explore new areas
        if action is None:
            action = self._explore()
            
        # Fallback: Random turn if stuck
        if action is None:
            action = random.choice(['turn_left', 'turn_right'])
            
        # Record action
        self.metrics['action_counts'][action] += 1
        return action

    def _should_shoot(self):
        x, y = self.world.agent_pos
        facing = self._get_facing_cell()
        
        if facing and self.knowledge_base[facing]['wumpus_prob'] > 0.8:
            self.metrics['wumpus_shots'] += 1
            self.metrics['total_reward'] -= 10  # Arrow cost
            return True
        return False

    def _plan_path_home(self):
        path = self._find_path((0, 0))
        if path:
            return self._next_move_from_path(path)
        return None

    def _explore(self):
        # Find safest unexplored cell
        target = self._select_exploration_target()
        if target:
            path = self._find_path(target)
            if path:
                return self._next_move_from_path(path)
        return None

    def _select_exploration_target(self):
        unexplored = [pos for pos in self.safe_cells if pos not in self.visited]
        if not unexplored:
            return None
            
        # Select target with lowest risk
        return min(unexplored, 
                  key=lambda p: self.knowledge_base[p]['pit_prob'] + self.knowledge_base[p]['wumpus_prob'])

    def _find_path(self, target):
        """A* pathfinding with risk awareness"""
        start = self.world.agent_pos
        open_set = {start}
        came_from = {}
        
        g_score = defaultdict(lambda: float('inf'))
        g_score[start] = 0
        
        f_score = defaultdict(lambda: float('inf'))
        f_score[start] = self._heuristic(start, target)
        
        while open_set:
            current = min(open_set, key=lambda p: f_score[p])
            
            if current == target:
                return self._reconstruct_path(came_from, current)
                
            open_set.remove(current)
            
            for neighbor in self._get_neighbors(current):
                tentative_g = g_score[current] + self._move_cost(current, neighbor)
                
                if tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + self._heuristic(neighbor, target)
                    if neighbor not in open_set:
                        open_set.add(neighbor)
                        
        return None

    def _move_cost(self, pos1, pos2):
        """Cost function considering risk"""
        base_cost = 1
        risk = self.knowledge_base[pos2]['pit_prob'] + self.knowledge_base[pos2]['wumpus_prob']
        return base_cost + (10 * risk * self.conservatism)

    def _heuristic(self, pos, target):
        """Manhattan distance with small noise for exploration"""
        dx = abs(pos[0] - target[0])
        dy = abs(pos[1] - target[1])
        return dx + dy + random.uniform(0, 0.1)

    def _get_neighbors(self, pos):
        x, y = pos
        neighbors = []
        for dx, dy in [(0,1), (1,0), (0,-1), (-1,0)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.world.grid_size and 0 <= ny < self.world.grid_size:
                neighbors.append((nx, ny))
        return neighbors

    def _reconstruct_path(self, came_from, current):
        path = []
        while current in came_from:
            path.append(current)
            current = came_from[current]
        path.reverse()
        return path

    def _next_move_from_path(self, path):
        if len(path) < 1:
            return None
            
        next_pos = path[0]
        current_pos = self.world.agent_pos
        dx = next_pos[0] - current_pos[0]
        dy = next_pos[1] - current_pos[1]
        
        desired_dir = None
        if dx == 1: desired_dir = 'right'
        elif dx == -1: desired_dir = 'left'
        elif dy == 1: desired_dir = 'down'
        elif dy == -1: desired_dir = 'up'
        
        if desired_dir == self.world.agent_dir:
            return 'forward'
        else:
            current_idx = ['right', 'down', 'left', 'up'].index(self.world.agent_dir)
            desired_idx = ['right', 'down', 'left', 'up'].index(desired_dir)
            return 'turn_right' if (desired_idx - current_idx) % 4 == 1 else 'turn_left'

    def _get_facing_cell(self):
        x, y = self.world.agent_pos
        if self.world.agent_dir == 'right' and x < self.world.grid_size - 1:
            return (x + 1, y)
        elif self.world.agent_dir == 'left' and x > 0:
            return (x - 1, y)
        elif self.world.agent_dir == 'up' and y > 0:
            return (x, y - 1)
        elif self.world.agent_dir == 'down' and y < self.world.grid_size - 1:
            return (x, y + 1)
        return None

    def get_metrics(self):
        return {
            **self.metrics,
            'exploration_rate': len(self.visited) / (self.world.grid_size ** 2),
            'avg_risk': np.mean([self.knowledge_base[p]['pit_prob'] + self.knowledge_base[p]['wumpus_prob'] 
                          for p in self.visited])
        }
    def move_forward(self):
        if self.world.move_forward():
            self.metrics['cells_explored'] += 1
        if self.world.percepts['breeze'] or self.world.percepts['stench']:
            self.metrics['risky_moves_made'] += 1
        else:
            self.metrics['safe_moves_made'] += 1

    def grab_gold(self):
        if self.world.grab_gold():
            self.metrics['gold_found'] = True
    
    def get_state_representation(self):
        """Create a simplified state representation for 
        training"""
        return (
            self.world.agent_pos,
            self.world.agent_dir,
            int(self.world.has_gold),
            int(self.world.has_arrow),
            tuple(self.world.percepts.values())
        )

    def receive_reward(self, reward):
        """Allow the agent to process rewards during training"""
        self.metrics['total_reward'] += reward

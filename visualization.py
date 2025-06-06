import pygame
import sys
import time
from pygame.locals import *

# Constants
CELL_SIZE = 100
MARGIN = 50
GRID_SIZE =4
STATUS_HEIGHT = 100
FONT_SIZE = 16
TITLE_FONT_SIZE = 32
SCREEN_WIDTH = GRID_SIZE * CELL_SIZE + 2 * MARGIN + 200

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GOLD = (255, 215, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
LIGHT_GREEN = (200, 255, 200)
LIGHT_BLUE = (173, 216, 230)
LIGHT_PINK = (255, 182, 193)
LAVENDER = (230, 230, 250)
GRAY = (200, 200, 200)

class GameVisualization:
    def __init__(self, world):
        pygame.init()  
        pygame.display.init() 
        pygame.font.init()  
        self.world = world
        self.grid_size = world.grid_size
        self.cell_size = 100
        self.margin = 50
        self.screen_width = self.grid_size * CELL_SIZE + 2 * MARGIN
        self.screen_height = self.grid_size * CELL_SIZE + 2 * MARGIN + STATUS_HEIGHT
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Wumpus World")
        self.font = None
        self.title_font = None
        try:
            self.font = pygame.font.SysFont('arial', 16)
            self.title_font = pygame.font.SysFont('arial', 24)
        except:
            try:
                self.font = pygame.font.Font(None, 16)  # None without quotes!
                self.title_font = pygame.font.Font(None, 24)
            except Exception as e:
                print(f"Font initialization failed: {e}")
                sys.exit(1)
        self.clock = pygame.time.Clock()
        self.auto_play = False
        self.last_update = 0
        self.update_interval = 0.5  # seconds

    def draw_metrics(self, metrics):
        """Display real-time agent metrics"""
        if not self.font:  # Ensure font exists
            return
        y_offset = 10
        for metric, value in metrics.items():
            text = f"{metric}: {value}"
            text_surface = self.font.render(text, True, (0, 0, 0))
            self.screen.blit(text_surface, (10, y_offset))
            y_offset += 20
    
    

    def draw_world(self):
        """Render the Wumpus world"""
        self.screen.fill(WHITE)
        
        # Draw grid cells
        for x in range(self.grid_size):
            for y in range(self.grid_size):
                rect = pygame.Rect(
                    MARGIN + x * CELL_SIZE,
                    MARGIN + y * CELL_SIZE,
                    CELL_SIZE,
                    CELL_SIZE
                )
                
                # Cell background color
                if (x, y) in self.world.visited:
                    color = LAVENDER
                elif (x, y) in self.world.safe_cells:
                    color = LIGHT_GREEN
                else:
                    color = WHITE
                
                pygame.draw.rect(self.screen, color, rect)
                pygame.draw.rect(self.screen, GRAY, rect, 1)
                
                # Draw cell contents
                self.draw_cell_contents(x, y)
        
        # Draw agent
        self.draw_agent()
        
        # Draw status panel
        self.draw_status()
        
        pygame.display.flip()

    def draw_cell_contents(self, x, y):
        """Draw pits, Wumpus, gold, and indicators"""
        center_x = MARGIN + x * CELL_SIZE + CELL_SIZE // 2
        center_y = MARGIN + y * CELL_SIZE + CELL_SIZE // 2
        cell = self.world.world[x][y]
        
        # Draw pit
        if cell["pit"]:
            pygame.draw.circle(self.screen, BLACK, (center_x, center_y), 20)
        
        # Draw Wumpus
        if cell.get("wumpus", False) and self.world.wumpus_alive:
            pygame.draw.polygon(self.screen, RED, [
                (center_x, center_y - 20),
                (center_x + 20, center_y + 20),
                (center_x - 20, center_y + 20)
            ])
        
        # Draw gold
        if cell["gold"]:
            pygame.draw.circle(self.screen, GOLD, (center_x, center_y), 15)
        
        # Draw stench indicator
        if (x, y) in self.world.stenchy_cells:
            stench_rect = pygame.Rect(
                MARGIN + x * CELL_SIZE + 5,
                MARGIN + y * CELL_SIZE + 5,
                10, 10
            )
            pygame.draw.rect(self.screen, LIGHT_PINK, stench_rect)
        
        # Draw breeze indicator
        if (x, y) in self.world.breezy_cells:
            breeze_rect = pygame.Rect(
                MARGIN + x * CELL_SIZE + CELL_SIZE - 15,
                MARGIN + y * CELL_SIZE + 5,
                10, 10
            )
            pygame.draw.rect(self.screen, LIGHT_BLUE, breeze_rect)

    def draw_agent(self):
        """Draw the agent with direction indicator"""
        x, y = self.world.agent_pos
        center_x = MARGIN + x * CELL_SIZE + CELL_SIZE // 2
        center_y = MARGIN + y * CELL_SIZE + CELL_SIZE // 2
        
        # Draw agent
        pygame.draw.circle(self.screen, BLUE, (center_x, center_y), 15)
        
        # Draw direction indicator
        indicator_length = 20
        if self.world.agent_dir == "up":
            end_pos = (center_x, center_y - indicator_length)
        elif self.world.agent_dir == "down":
            end_pos = (center_x, center_y + indicator_length)
        elif self.world.agent_dir == "left":
            end_pos = (center_x - indicator_length, center_y)
        else:  # right
            end_pos = (center_x + indicator_length, center_y)
        
        pygame.draw.line(self.screen, WHITE, (center_x, center_y), end_pos, 3)

    def draw_status(self):
        """Draw game status information"""
        status_y = MARGIN + self.grid_size * CELL_SIZE + 10
        
        # Agent status
        status_text = (
            f"Position: {self.world.agent_pos} | "
            f"Direction: {self.world.agent_dir} | "
            f"Gold: {'Yes' if self.world.has_gold else 'No'} | "
            f"Arrow: {'Yes' if self.world.has_arrow else 'No'} | "
            f"Wumpus: {'Alive' if self.world.wumpus_alive else 'Dead'}"
        )
        status_surface = self.font.render(status_text, True, BLACK)
        self.screen.blit(status_surface, (MARGIN, status_y))
        
        # Percepts
        percepts_y = status_y + 25
        percepts_text = "Percepts: "
        if self.world.percepts["stench"]:
            percepts_text += "Stench "
        if self.world.percepts["breeze"]:
            percepts_text += "Breeze "
        if self.world.percepts["glitter"]:
            percepts_text += "Glitter "
        if self.world.percepts["bump"]:
            percepts_text += "Bump "
        if self.world.percepts["scream"]:
            percepts_text += "Scream "
        
        percepts_surface = self.font.render(percepts_text, True, BLACK)
        self.screen.blit(percepts_surface, (MARGIN, percepts_y))
        
        # Controls info
        controls_y = percepts_y +25
        controls_text = (
            "Controls: Arrows to move/turn | SPACE to toggle auto-play | "
            "G to grab gold | S to shoot"
        )
        controls_surface = self.font.render(controls_text, True, BLACK)
        self.screen.blit(controls_surface, (MARGIN, controls_y))
        
        # Game over message
        game_status = self.world.is_game_over()
        if game_status != "continue":
            message = "You Win!" if game_status == "win" else "Game Over!"
            message_surface = self.title_font.render(message, True, RED)
            message_rect = message_surface.get_rect(
                center=(self.screen_width // 2, self.screen_height - 50))
            self.screen.blit(message_surface, message_rect)

    def handle_events(self):
        """Handle keyboard and window events"""
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                elif event.key == K_SPACE:
                    self.auto_play = not self.auto_play
                elif not self.auto_play:
                    if event.key == K_UP:
                        self.world.move_forward()
                    elif event.key == K_LEFT:
                        self.world.turn_left()
                    elif event.key == K_RIGHT:
                        self.world.turn_right()
                    elif event.key == K_g and self.world.percepts["glitter"]:
                        self.world.grab_gold()
                    elif event.key == K_s and self.world.has_arrow:
                        self.world.shoot_arrow()

    def auto_play_step(self):
        """Execute one step of autonomous agent logic"""
        current_time = time.time()
        if current_time - self.last_update < self.update_interval:
            return
        
        self.last_update = current_time
        game_status = self.world.is_game_over()
        if game_status != "continue":
            return
        
        # If glitter, grab gold
        if self.world.percepts["glitter"]:
            self.world.grab_gold()
            return
        
        # If stench and have arrow, consider shooting
        if (self.world.percepts["stench"] and self.world.has_arrow and 
            self.world.wumpus_alive):
            x, y = self.world.agent_pos
            facing_pos = None
            
            if self.world.agent_dir == "up" and y > 0:
                facing_pos = (x, y - 1)
            elif self.world.agent_dir == "down" and y < self.grid_size - 1:
                facing_pos = (x, y + 1)
            elif self.world.agent_dir == "left" and x > 0:
                facing_pos = (x - 1, y)
            elif self.world.agent_dir == "right" and x < self.grid_size - 1:
                facing_pos = (x + 1, y)
            
            if (facing_pos and 
                self.world.knowledge_base[facing_pos]["wumpus"] != False):
                self.world.shoot_arrow()
                return
        
        # Get next safe move
        next_pos = self.world.get_safe_move()
        if next_pos:
            action = self.world.get_direction_to_move(next_pos)
            
            if action == "forward":
                self.world.move_forward()
            elif action == "left":
                self.world.turn_left()
            elif action == "right":
                self.world.turn_right()
        else:
            # No safe moves found, try to return home if we have gold
            if self.world.has_gold:
                path = self.world.find_path(self.world.agent_pos, (0, 0))
                if path and len(path) > 1:
                    next_pos = path[1]
                    action = self.world.get_direction_to_move(next_pos)
                    
                    if action == "forward":
                        self.world.move_forward()
                    elif action == "left":
                        self.world.turn_left()
                    elif action == "right":
                        self.world.turn_right()

    def run(self):
        """Main game loop"""
        while True:
            self.handle_events()
            
            if self.auto_play:
                self.auto_play_step()
            
            self.draw_world()
            self.clock.tick(30)


    
  
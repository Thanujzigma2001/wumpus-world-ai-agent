from wumpus_world import WumpusWorld
from visualization import GameVisualization
from agent import WumpusAgent
from trainer_agent import AgentTrainer
import pygame
import sys

def main():
    # Initialize game components
    world = WumpusWorld(grid_size=4)
    agent = WumpusAgent(world)
    game = GameVisualization(world)
    
    # Game state control
    running = True
    auto_play = True  # Set to False for manual control
    clock = pygame.time.Clock()
    
    # Main game loop
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    auto_play = not auto_play  # Toggle auto/manual mode
                elif not auto_play:  # Manual controls
                    if event.key == pygame.K_UP:
                        world.move_forward()
                    elif event.key == pygame.K_LEFT:
                        world.turn_left()
                    elif event.key == pygame.K_RIGHT:
                        world.turn_right()
                    elif event.key == pygame.K_g:
                        world.grab_gold()
                    elif event.key == pygame.K_s:
                        world.shoot_arrow()
        def draw_metrics(self):
            font = pygame.font.SysFont('Arial', 16)
            metrics = [
                f"Cells Explored: {self.agent.metrics['cells_explored']}",
                f"Safe Moves: {self.agent.metrics['safe_moves_made']}",
                f"Risky Moves: {self.agent.metrics['risky_moves_made']}",
                f"Gold Found: {'Yes' if self.agent.metrics['gold_found'] else 'No'}"
            ]
    
        for i, text in enumerate(metrics):
            text_surface = font.render(text, True, (0, 0, 0))
            self.screen.blit(text_surface, (10, 10 + i * 20))
        
        # AI agent control
        if auto_play:
            action = agent.decide_action()
            if action == "forward":
                world.move_forward()
            elif action == "turn_left":
                world.turn_left()
            elif action == "turn_right":
                world.turn_right()
            elif action == "grab":
                world.grab_gold()
            elif action == "shoot":
                world.shoot_arrow()
            elif action == "climb":
                if world.has_gold and world.agent_pos == (0, 0):
                    print("Agent climbed out with gold!")
            
            agent.update_knowledge()
        
        # Update game state
        status = world.is_game_over()
        if status != "continue":
            print(f"Game Over: {'Win!' if status == 'win' else 'Lose!'}")
            running = False
        
        # Render the game
        game.draw_world()
        
        # Display control mode
        font = pygame.font.SysFont('Arial', 20)
        mode_text = font.render(
            f"Mode: {'AUTO' if auto_play else 'MANUAL'}",
            True, 
            (0, 0, 255))
        game.screen.blit(mode_text, (10, 10))
        
        pygame.display.flip()
        clock.tick(5)  # Control game speed (5 FPS)

        
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()


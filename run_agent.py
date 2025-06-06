import pickle
import pygame
import sys
from wumpus_world import WumpusWorld
from visualization import GameVisualization
from agent import WumpusAgent

def load_trained_agent(model_path="saved_models/final_agent.pkl"):
    try:
        with open(model_path, 'rb') as f:
            agent_data = pickle.load(f)
        
        world = WumpusWorld(grid_size=4)
        agent = WumpusAgent(world)
        agent.knowledge_base = agent_data['knowledge_base']
        if 'hyperparameters' in agent_data:
            agent.conservatism = agent_data['hyperparameters'].get('conservatism', 0.5)
        return agent, world
    except Exception as e:
        print(f"Error loading agent: {e}")
        sys.exit(1)

def run_trained_agent():
    try:
        pygame.init()
        agent, world = load_trained_agent()
        game = GameVisualization(world)
        
        running = True
        clock = pygame.time.Clock()
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
            
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
                    print("Mission accomplished!")
                    running = False
            
            agent.update_knowledge()
            
            status = world.is_game_over()
            if status != "continue":
                print(f"Game Over: {'Win!' if status == 'win' else 'Lose!'}")
                running = False
            
            game.draw_world()
            game.draw_metrics({
                'Position': world.agent_pos,
                'Direction': world.agent_dir,
                'Has Gold': str(world.has_gold),
                'Arrows': str(world.has_arrow),
                'Score': agent.metrics.get('total_reward', 0)
            })
            
            pygame.display.flip()
            clock.tick(5)  # 5 FPS
        
    except Exception as e:
        print(f"Error during execution: {e}")
    finally:
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    run_trained_agent()
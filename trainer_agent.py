import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict, deque
import random
import pickle
import os
from tqdm import tqdm
from agent import WumpusAgent
from wumpus_world import WumpusWorld

class WumpusAgentTrainer:
    def __init__(self, grid_size=4, num_episodes=1000):
        self.grid_size = grid_size
        self.num_episodes = num_episodes
        
        # Training metrics storage
        self.metrics = {
            'episode_rewards': [],
            'steps_per_episode': [],
            'success_rate': [],
            'exploration_rate': [],
            'gold_retrieval_rate': [],
            'pit_deaths': 0,
            'wumpus_deaths': 0,
            'heatmap': np.zeros((grid_size, grid_size))
        }
        
        # Hyperparameters
        self.hyperparams = {
            'initial_exploration': 0.3,
            'final_exploration': 0.01,
            'exploration_decay': 0.9995,
            'learning_rate': 0.1,
            'discount_factor': 0.95,
            'conservatism': 0.7  # Risk aversion factor
        }
        
        # Create directories for outputs
        os.makedirs("saved_models", exist_ok=True)
        os.makedirs("training_plots", exist_ok=True)

    def train(self):
        exploration_rate = self.hyperparams['initial_exploration']
        successful_episodes = 0
        
        for episode in tqdm(range(self.num_episodes), desc="Training Agent"):
            world = WumpusWorld(grid_size=self.grid_size)
            agent = WumpusAgent(world)
            agent.conservatism = self.hyperparams['conservatism']
            
            episode_reward = 0
            steps = 0
            gold_grabbed = False
            done = False
            
            while not done and steps < 200:  # Max steps per episode
                # Exploration vs Exploitation
                if random.random() < exploration_rate:
                    action = random.choice(['forward', 'turn_left', 'turn_right'])
                else:
                    action = agent.decide_action()
                
                # Execute action and get reward
                reward, action_executed = self._execute_action(world, agent, action)
                episode_reward += reward
                steps += 1
                
                # Update heatmap
                self.metrics['heatmap'][world.agent_pos] += 1
                
                # Check for gold collection
                if action == 'grab' and world.has_gold:
                    gold_grabbed = True
                
                # Check termination conditions
                status = world.is_game_over()
                if status != "continue":
                    if status == "win":
                        successful_episodes += 1
                        reward += 1000  # Final success bonus
                    done = True
                
                # Update agent knowledge
                agent.update_knowledge()
                
                # Decrease exploration rate
                exploration_rate = max(self.hyperparams['final_exploration'],
                                    exploration_rate * self.hyperparams['exploration_decay'])
            
            # Store episode metrics
            self._update_metrics(world,episode_reward, steps, gold_grabbed, 
                               successful_episodes, episode, status)
            
            # Save model periodically
            if (episode + 1) % 100 == 0:
                self._save_model(agent, episode + 1)
                self._generate_intermediate_plots()
        
        # Final training outputs
        self._save_final_model(agent)
        self._generate_final_report()
        return agent

    def _execute_action(self, world, agent, action):
        """Execute action and return appropriate reward"""
        reward = -1  # Default step penalty
        action_executed = False
        
        if action == "forward":
            if world.move_forward():
                reward = -0.2
                action_executed = True
            else:
                reward = -2  # Bump penalty
        elif action == "turn_left":
            world.turn_left()
            reward = -0.1
            action_executed = True
        elif action == "turn_right":
            world.turn_right()
            reward = -0.1
            action_executed = True
        elif action == "grab":
            if world.grab_gold():
                reward = 300  # Gold reward
                action_executed = True
            else:
                reward = -5  # Useless grab penalty
        elif action == "shoot":
            if world.shoot_arrow():
                reward = 100  # Wumpus kill reward
                action_executed = True
            else:
                reward = -20  # Missed shot penalty
        
        # Additional reward shaping
        if action_executed:
            # Reward exploration of new cells
            if world.agent_pos not in agent.visited:
                reward += 5
            
            # Penalize risky moves
            risk = agent.knowledge_base[world.agent_pos]['pit_prob'] + \
                   agent.knowledge_base[world.agent_pos]['wumpus_prob']
            reward -= risk * 10 * agent.conservatism
        
        return reward, action_executed

    def _update_metrics(self, world,reward, steps, gold_grabbed, successes, episode, status):
        """Store all training metrics"""
        self.metrics['episode_rewards'].append(reward)
        self.metrics['steps_per_episode'].append(steps)
        self.metrics['success_rate'].append(successes / (episode + 1))
        self.metrics['gold_retrieval_rate'].append(int(gold_grabbed))
        
        if status == "lose":
            x, y = world.agent_pos
            if world.world[x][y]["pit"]:
                self.metrics['pit_deaths'] += 1
            else:
                self.metrics['wumpus_deaths'] += 1

    def _save_model(self, agent, episode):
        """Save agent state periodically"""
        filename = f"saved_models/agent_episode_{episode}.pkl"
        with open(filename, 'wb') as f:
            pickle.dump({
                'knowledge_base': agent.knowledge_base,
                'metrics': agent.metrics,
                'hyperparameters': self.hyperparams,
                'training_metrics': self.metrics
            }, f)

    def _save_final_model(self, agent):
        """Save final trained agent"""
        with open("saved_models/final_agent.pkl", 'wb') as f:
            pickle.dump({
                'knowledge_base': agent.knowledge_base,
                'metrics': agent.metrics,
                'hyperparameters': self.hyperparams,
                'training_metrics': self.metrics
            }, f)

    def _generate_intermediate_plots(self):
        """Generate periodic training plots"""
        plt.figure(figsize=(15, 10))
        
        # Reward tracking
        plt.subplot(2, 2, 1)
        plt.plot(self.metrics['episode_rewards'])
        plt.title("Episode Rewards")
        plt.xlabel("Episode")
        plt.ylabel("Total Reward")
        
        # Success rate
        plt.subplot(2, 2, 2)
        plt.plot(self.metrics['success_rate'])
        plt.title("Success Rate")
        plt.xlabel("Episode")
        plt.ylabel("Win Percentage")
        plt.ylim(0, 1)
        
        # Steps per episode
        plt.subplot(2, 2, 3)
        plt.plot(self.metrics['steps_per_episode'])
        plt.title("Steps per Episode")
        plt.xlabel("Episode")
        plt.ylabel("Steps")
        
        # Exploration rate
        plt.subplot(2, 2, 4)
        plt.plot(self.metrics['exploration_rate'])
        plt.title("Exploration Rate")
        plt.xlabel("Episode")
        plt.ylabel("Rate")
        
        plt.tight_layout()
        plt.savefig(f"training_plots/training_progress.png")
        plt.close()

    def _generate_final_report(self):
        """Generate comprehensive final report"""
        # Training curves
        self._generate_intermediate_plots()
        
        # Heatmap visualization
        plt.figure(figsize=(8, 8))
        plt.imshow(self.metrics['heatmap'], cmap='hot', interpolation='nearest')
        plt.title("Exploration Heatmap")
        plt.colorbar()
        plt.savefig("training_plots/exploration_heatmap.png")
        plt.close()
        
        # Text summary
        with open("training_plots/summary.txt", "w") as f:
            f.write(f"Training Summary ({self.num_episodes} episodes)\n")
            f.write("="*50 + "\n")
            f.write(f"Final Success Rate: {self.metrics['success_rate'][-1]:.2%}\n")
            f.write(f"Gold Retrieval Rate: {np.mean(self.metrics['gold_retrieval_rate']):.2%}\n")
            f.write(f"Average Steps per Episode: {np.mean(self.metrics['steps_per_episode']):.1f}\n")
            f.write(f"Pit Deaths: {self.metrics['pit_deaths']}\n")
            f.write(f"Wumpus Deaths: {self.metrics['wumpus_deaths']}\n\n")
            f.write("Hyperparameters:\n")
            for k, v in self.hyperparams.items():
                f.write(f"{k}: {v}\n")

if __name__ == "__main__":
    trainer = WumpusAgentTrainer(num_episodes=1000)
    trained_agent = trainer.train()
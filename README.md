# wumpus-world-ai-agent
A Python AI agent that autonomously navigates the Wumpus World game, finds gold, and returns home safely
# 🏆 Wumpus World AI Agent

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)]()
[![Pygame](https://img.shields.io/badge/pygame-2.6+-green.svg)]()

An intelligent agent that autonomously navigates the Wumpus World environment, avoiding dangers while collecting gold.

![Demo GIF](docs/demo.gif)

## Features
- 🧠 Probabilistic reasoning for threat detection
- 🗺️ A* pathfinding with risk-adjusted costs
- 📊 Training pipeline with performance metrics
- 🎮 Pygame visualization

## Quick Start
```bash
git clone https://github.com/yourusername/wumpus-world-ai-agent.git
cd wumpus-world-ai-agent
pip install -r requirements.txt

# Run trained agent
python src/run_agent.py

# Train new agent
python src/trainer_agent.py

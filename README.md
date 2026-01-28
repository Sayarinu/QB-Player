# Queen's Blood AI Simulator

A high-fidelity implementation of the Queen's Blood card game from Final Fantasy VII Rebirth, including a complete game engine, card database, and Reinforcement Learning (RL) training pipeline.

## Features
- **Accurate Game Engine**: Follows all official rules including rank increases, tile captures, and replacement mechanics.
- **145 Card Database**: Comprehensive stats for all cards from the base game.
- **RL Environment**: Gymnasium-compatible environment for training AI agents.
- **PPO Agent**: Reinforcement learning agent using Proximal Policy Optimization.
- **Baseline Agents**: Random and Greedy heuristic agents for benchmarking.

## Project Structure
- `queens_blood_ai/game/`: Core rules engine (Board, Card, Deck, Effects).
- `queens_blood_ai/data/`: Card database and pre-made decks.
- `queens_blood_ai/agents/`: Agent implementations (Baseline & RL).
- `queens_blood_ai/training/`: RL environment and PPO training loop.
- `queens_blood_ai/play.py`: Visual/ASCII script to watch games.
- `queens_blood_ai/train.py`: Main training script.

## Installation
```bash
pip install -r queens_blood_ai/requirements.txt
```

## Usage

### Watch a Match
To watch two random agents play, run this from the project root:
```bash
export PYTHONPATH=$PYTHONPATH:.
python3 -m queens_blood_ai.play --render
```

### Train the AI
```bash
export PYTHONPATH=$PYTHONPATH:.
python3 -m queens_blood_ai.train --config queens_blood_ai/configs/training_config.yaml
```

### Run Tests
```bash
export PYTHONPATH=$PYTHONPATH:.
pytest queens_blood_ai/tests/
```

## Card Database
The `cards_database.json` contains the following fields for each card:
- `id`: Unique identifier (#001 - #145).
- `name`: Card name.
- `cost`: Pawn rank required to play.
- `power`: Base power value.
- `rank_positions`: Relative coordinates for rank activation.
- `ability_positions`: Relative coordinates for ability effects.
- `description`: In-game text description.

## AI Implementation Details
The AI uses a **Convolutional Neural Network (CNN)** to process the spatial layout of the board, combined with an **Embedding layer** for the cards in hand. It is trained via **Self-Play** using the PPO algorithm.

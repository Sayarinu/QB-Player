import argparse
import json
import os
from dotenv import load_dotenv

# Load env variables from .env file (if present)
load_dotenv()

from queens_blood_ai.training.trainer import PPOTrainer
from queens_blood_ai.game.card import Card

def load_cards(path):
    with open(path, 'r') as f:
        data = json.load(f)
    return [Card.from_dict(d) for d in data]

def main():
    parser = argparse.ArgumentParser(description="Train Queen's Blood AI")
    parser.add_argument("--config", type=str, default="queens_blood_ai/configs/training_config.yaml")
    parser.add_argument("--continuous", action="store_true", help="Run training continuously indefinitely")
    args = parser.parse_args()
    
    print("Loading card database...")
    cards = load_cards("queens_blood_ai/data/cards_database.json")
    
    print("Initialising PPO Trainer...")
    trainer = PPOTrainer(args.config, cards, continuous=args.continuous)
    
    print("Starting Reinforcement Learning loop...")
    trainer.train()
    
if __name__ == "__main__":
    main()

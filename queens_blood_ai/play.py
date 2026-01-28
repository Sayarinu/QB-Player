import argparse
import time
import json
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from queens_blood_ai.game.game import Game, Player
from queens_blood_ai.game.deck import Deck
from queens_blood_ai.game.card import Card
import random

def load_cards(path):
    with open(path, 'r') as f:
        data = json.load(f)
    return [Card.from_dict(d) for d in data]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--render", action="store_true")
    args = parser.parse_args()
    
    cards = load_cards("queens_blood_ai/data/cards_database.json")
    
    # Randomly sample 15 cards for each player's deck
    deck1 = Deck(random.sample(cards, 15))
    deck2 = Deck(random.sample(cards, 15))
    
    game = Game(deck1, deck2)
    
    print("Game Started!")
    while not game.game_over:
        moves = game.get_legal_moves(game.current_turn)
        if moves:
            # Simple Greedy Agent: pick move that maximizes current total power
            best_move = None
            max_power = -100
            
            for move in moves:
                # Mock a step (copying state is expensive, so we just heuristic)
                card_idx, r, c = move
                card = game.players[game.current_turn]["hand"][card_idx]
                # Priority: 1. Maximize card power, 2. Prefer expanding towards center
                power = card.power + (5 - c if game.current_turn == Player.PLAYER1 else c)
                if power > max_power:
                    max_power = power
                    best_move = move
            
            move = best_move
            print(f"Player {game.current_turn} plays {game.players[game.current_turn]['hand'][move[0]].name} at {move[1:]}")
            game.step(move)
        else:
            print(f"Player {game.current_turn} passes.")
            game.step(None)
            
        if args.render:
            # Simple ASCII render
            for r in range(game.board.height):
                row_str = ""
                for c in range(game.board.width):
                    owner = game.board.get_owner(r, c)
                    owner_name = "P1" if owner == Player.PLAYER1 else "P2" if owner == Player.PLAYER2 else ".."
                    rank = game.board.get_rank(r, c, owner) if owner != Player.NEUTRAL else 0
                    card = game.board.cards[r][c]
                    
                    if card:
                        power_str = f"{card.adjusted_power:2d}"
                        name_str = card.name[:3]
                    else:
                        power_str = "  "
                        name_str = "   "
                        
                    row_str += f"[{owner_name} R{rank} {name_str}:{power_str}] "
                print(row_str)
            print("-" * 20)
            time.sleep(1)

    s1, s2 = game.get_final_scores()
    print(f"Game Over! Final Score: P1 {s1} - P2 {s2}")

if __name__ == "__main__":
    main()
